// TaskFlow - frontend con Alpine.js
// Todo el estado de la página vive en este objeto. Alpine lo "conecta" al HTML:
// cuando cambia una propiedad (por ejemplo this.tasks), la pantalla se actualiza sola.

const STATUSES = [
  { value: "pendiente", label: "Pendiente", icon: "bi-circle" },
  { value: "en_progreso", label: "En progreso", icon: "bi-arrow-repeat" },
  { value: "completada", label: "Completada", icon: "bi-check2-circle" },
];
const PRIORITIES = [
  { value: "baja", label: "Baja", color: "success" },
  { value: "media", label: "Media", color: "warning" },
  { value: "alta", label: "Alta", color: "danger" },
];

// Convierte los errores de la API ({"error": true, "detail": ...}, ver core/exceptions.py)
// en un texto legible. "detail" puede ser un texto, una lista o un {campo: [mensajes]}.
function errorMessage(data) {
  const msgs = [];
  const walk = (value, field) => {
    if (typeof value === "string") {
      msgs.push(field && !["detail", "non_field_errors"].includes(field) ? `${field}: ${value}` : value);
    } else if (Array.isArray(value)) {
      value.forEach((v) => walk(v, field));
    } else if (value && typeof value === "object") {
      for (const [k, v] of Object.entries(value)) {
        if (!["error", "code", "messages"].includes(k)) walk(v, k);
      }
    }
  };
  walk(data?.detail ?? data);
  return msgs.join(" · ") || "Error inesperado.";
}

document.addEventListener("alpine:init", () => {
  Alpine.data("taskflow", () => ({
    STATUSES,
    PRIORITIES,

    // Sesión: los JWT de la Clase 6 se guardan en el navegador
    access: localStorage.getItem("access"),
    refresh: localStorage.getItem("refresh"),
    username: localStorage.getItem("username") || "",

    // Pantalla de login
    mode: "login",
    form: { username: "", email: "", password: "" },

    // Datos
    projects: [],
    tasks: [],
    stats: {},
    page: { number: 1, count: 0, next: null, previous: null },
    filters: { project: null, search: "", status: "", priority: "", ordering: "-created_at" },
    overdueOnly: false,

    // Interfaz
    loading: false,
    taskForm: null,     // null = modal cerrado; un objeto = modal abierto
    projectForm: null,
    toasts: [],
    dark: localStorage.getItem("theme") === "dark",

    // Alpine llama a init() automáticamente al arrancar
    async init() {
      this.applyTheme();
      // ¿Volvemos del login con Google? (Clase 7) La sesión de Django ya existe:
      // la cambiamos por un par de JWT.
      if (new URLSearchParams(location.search).has("google")) {
        history.replaceState(null, "", "/");
        try {
          const data = await this.api("/api/auth/social/jwt/");
          this.saveTokens(data);
          this.username = "Google #" + this.userIdFromToken();
          localStorage.setItem("username", this.username);
        } catch (e) {
          this.notify("No se pudo ingresar con Google: " + e.message, false);
        }
      }
      if (this.access) this.loadAll();
    },

    // ---------- Comunicación con la API ----------

    // Envuelve fetch: agrega el token, convierte a JSON y lanza un Error si la respuesta no es 2xx.
    async api(url, options = {}, retry = true) {
      const headers = { "Content-Type": "application/json" };
      if (this.access) headers["Authorization"] = `Bearer ${this.access}`;
      const response = await fetch(url, { ...options, headers });

      // Token vencido (dura 30 min): pedimos uno nuevo con el refresh y reintentamos una vez
      if (response.status === 401 && this.refresh && retry) {
        if (await this.refreshToken()) return this.api(url, options, false);
        this.logout();
        throw new Error("La sesión expiró, volvé a ingresar.");
      }

      const data = response.status === 204 ? null : await response.json().catch(() => null);
      if (!response.ok) throw new Error(errorMessage(data));
      return data;
    },

    async refreshToken() {
      const response = await fetch("/api/token/refresh/", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ refresh: this.refresh }),
      });
      if (!response.ok) return false;
      this.saveTokens(await response.json());
      return true;
    },

    saveTokens({ access, refresh }) {
      this.access = access;
      localStorage.setItem("access", access);
      if (refresh) {  // con ROTATE_REFRESH_TOKENS también llega un refresh nuevo
        this.refresh = refresh;
        localStorage.setItem("refresh", refresh);
      }
    },

    // Un JWT no está cifrado: el medio es JSON en base64 y cualquiera lo puede leer
    userIdFromToken() {
      return JSON.parse(atob(this.access.split(".")[1])).user_id;
    },

    // ---------- Autenticación ----------

    async login() {
      this.loading = true;
      try {
        const data = await this.api("/api/token/", {
          method: "POST",
          body: JSON.stringify({ username: this.form.username, password: this.form.password }),
        });
        this.saveTokens(data);
        this.username = this.form.username;
        localStorage.setItem("username", this.username);
        this.form = { username: "", email: "", password: "" };
        this.loadAll();
      } catch (e) {
        this.notify(e.message, false);
      } finally {
        this.loading = false;
      }
    },

    async register() {
      this.loading = true;
      try {
        await this.api("/api/register/", { method: "POST", body: JSON.stringify(this.form) });
        this.notify("¡Cuenta creada! Ingresando...");
        await this.login();
      } catch (e) {
        this.notify(e.message, false);
      } finally {
        this.loading = false;
      }
    },

    logout() {
      localStorage.removeItem("access");
      localStorage.removeItem("refresh");
      localStorage.removeItem("username");
      this.access = this.refresh = null;
      this.projects = [];
      this.tasks = [];
      this.mode = "login";
    },

    // ---------- Proyectos y tareas ----------

    async loadAll() {
      await this.loadProjects();
      await this.loadTasks(1);
    },

    async loadProjects() {
      // La API pagina de a 5: seguimos los links "next" hasta traer todos
      let url = "/api/projects/";
      const all = [];
      try {
        while (url) {
          const data = await this.api(url);
          all.push(...data.results);
          url = data.next;
        }
        this.projects = all;
      } catch (e) {
        this.notify(e.message, false);
      }
    },

    async loadTasks(number = 1) {
      this.loading = true;
      try {
        let data;
        if (this.overdueOnly) {
          data = await this.api(`/api/tasks/overdue/?page=${number}`);
        } else {
          // Los filtros se mandan como parámetros de la URL (django-filter, Clase 5)
          const params = new URLSearchParams({ page: number, ordering: this.filters.ordering });
          if (this.filters.project) params.set("project", this.filters.project);
          if (this.filters.status) params.set("status", this.filters.status);
          if (this.filters.priority) params.set("priority", this.filters.priority);
          if (this.filters.search) params.set("search", this.filters.search);
          data = await this.api(`/api/tasks/?${params}`);
        }
        this.tasks = data.results;
        this.page = { number, count: data.count, next: data.next, previous: data.previous };
        this.loadStats();
      } catch (e) {
        this.notify(e.message, false);
      } finally {
        this.loading = false;
      }
    },

    // Una consulta por estado: solo nos interesa el "count" de la respuesta paginada
    async loadStats() {
      const base = this.filters.project ? `&project=${this.filters.project}` : "";
      for (const s of STATUSES) {
        const data = await this.api(`/api/tasks/?status=${s.value}${base}`);
        this.stats[s.value] = data.count;
      }
    },

    selectProject(id) {
      this.overdueOnly = false;
      this.filters.project = id;
      this.loadTasks(1);
    },

    showOverdue() {
      this.overdueOnly = true;
      this.filters.project = null;
      this.loadTasks(1);
    },

    openTaskForm(task = null) {
      this.taskForm = task
        ? { ...task, due_date: task.due_date || "", originalDueDate: task.due_date || "" }
        : { project: this.filters.project || "", title: "", description: "", priority: "media", due_date: "" };
    },

    async saveTask() {
      const f = this.taskForm;
      const body = {
        project: f.project,
        title: f.title,
        description: f.description,
        priority: f.priority,
        due_date: f.due_date || null,  // la API espera null, no un texto vacío
      };
      // Si no la tocamos, no la mandamos: una fecha ya pasada no pasaría validate_due_date
      if (f.id && f.due_date === f.originalDueDate) delete body.due_date;
      // "completada" pasa por /complete/, que aplica la regla de negocio (Clase 4)
      if (f.id && f.status !== "completada") body.status = f.status;
      try {
        if (f.id) {
          await this.api(`/api/tasks/${f.id}/`, { method: "PATCH", body: JSON.stringify(body) });
          if (f.status === "completada") await this.api(`/api/tasks/${f.id}/complete/`, { method: "POST" });
        } else {
          await this.api("/api/tasks/", { method: "POST", body: JSON.stringify(body) });
        }
        this.taskForm = null;
        this.notify(f.id ? "Tarea actualizada" : "Tarea creada");
        this.loadAll();
      } catch (e) {
        this.notify(e.message, false);  // ej.: 403 si no sos admin del proyecto
      }
    },

    async complete(task) {
      try {
        await this.api(`/api/tasks/${task.id}/complete/`, { method: "POST" });
        this.notify(`"${task.title}" completada 🎉`);
        this.loadTasks(this.page.number);
      } catch (e) {
        this.notify(e.message, false);
      }
    },

    async remove(task) {
      if (!confirm(`¿Borrar la tarea "${task.title}"?`)) return;
      try {
        await this.api(`/api/tasks/${task.id}/`, { method: "DELETE" });
        this.notify("Tarea borrada");
        this.loadAll();
      } catch (e) {
        this.notify(e.message, false);
      }
    },

    openProjectForm() {
      this.projectForm = { name: "", description: "" };
    },

    async saveProject() {
      try {
        const project = await this.api("/api/projects/", { method: "POST", body: JSON.stringify(this.projectForm) });
        this.projectForm = null;
        this.notify(`Proyecto "${project.name}" creado`);
        await this.loadProjects();
        this.selectProject(project.id);
      } catch (e) {
        this.notify(e.message, false);
      }
    },

    // ---------- Ayudantes para el HTML ----------

    title() {
      if (this.overdueOnly) return "Tareas vencidas";
      return this.filters.project ? this.projectName(this.filters.project) : "Todas las tareas";
    },
    projectName(id) {
      return this.projects.find((p) => p.id == id)?.name ?? `Proyecto #${id}`;
    },
    priority(value) {
      return PRIORITIES.find((p) => p.value === value) ?? PRIORITIES[1];
    },
    status(value) {
      return STATUSES.find((s) => s.value === value) ?? STATUSES[0];
    },
    formatDate(iso) {
      return new Date(iso + "T00:00:00").toLocaleDateString("es-AR");
    },

    notify(text, ok = true) {
      const id = Date.now() + Math.random();
      this.toasts.push({ id, text, ok });
      setTimeout(() => (this.toasts = this.toasts.filter((t) => t.id !== id)), 4000);
    },

    toggleTheme() {
      this.dark = !this.dark;
      localStorage.setItem("theme", this.dark ? "dark" : "light");
      this.applyTheme();
    },
    applyTheme() {
      document.documentElement.dataset.bsTheme = this.dark ? "dark" : "light";
    },
  }));
});

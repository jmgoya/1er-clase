# Importamos las librerías estándar de Python para manejar diferentes formatos de archivos.
import csv
import json
import xml.etree.ElementTree as ET

# BaseCommand es la clase que Django exige heredar para que este script
# cuente como un comando personalizado de manage.py.
from django.core.management.base import BaseCommand

# Importamos el modelo Task donde guardaremos los datos en la base de datos.
from core.models import Task


class Command(BaseCommand):
    # El atributo help proporciona una descripción corta que se muestra
    # cuando alguien ejecuta 'python manage.py help <nombre_del_comando>'.
    help = "Importa tareas desde múltiples proveedores (JSON, CSV, XML)"

    # El método handle es el punto de entrada. Es el código que se ejecuta
    # automáticamente cuando corremos el comando en la terminal.
    def handle(self, *args, **options):
        total = 0  # Inicializamos un contador para el total de tareas importadas con éxito.
        
        # Llamamos a los submétodos para cada tipo de archivo y sumamos los resultados.
        # Gracias a los bloques try/except dentro de cada submétodo, garantizamos que si un 
        # proveedor falla (ej. archivo faltante o corrupto), los demás igual se ejecuten.
        total += self._import_json("data/tasks_provider_a.json", source="proveedor_a")
        total += self._import_csv("data/tasks_provider_b.csv", source="proveedor_b")
        total += self._import_xml("data/tasks_provider_c.xml", source="proveedor_c")
        
        # self.stdout.write y self.style.SUCCESS imprimen un mensaje de éxito en la consola.
        self.stdout.write(self.style.SUCCESS(f"Importación finalizada: {total} tareas cargadas"))

    # El guion bajo al inicio de '_import_json' indica por convención que es un método
    # de "uso interno" de la clase y no forma parte de la interfaz pública del comando.
    def _import_json(self, path, source):
        count = 0
        try:
            # Abrimos el archivo en modo lectura con codificación UTF-8.
            with open(path, encoding="utf-8") as f:
                # Convertimos el contenido JSON en una lista/diccionario de Python.
                data = json.load(f)
                
                for item in data:  # Recorremos cada elemento del archivo JSON.
                    self._crear_task(item, source)  # Llamamos al método que lo guarda en la BD.
                    count += 1
                    
        # Atrapamos errores si el archivo no existe o el JSON está mal formateado.
        except (FileNotFoundError, json.JSONDecodeError) as e:
            # self.stderr.write imprime errores en la consola (generalmente en color rojo).
            self.stderr.write(self.style.ERROR(f"Error importando {path}: {e}"))
            
        return count  # Devolvemos cuántas tareas se importaron exitosamente de este archivo.

    def _import_csv(self, path, source):
        count = 0
        try:
            with open(path, encoding="utf-8") as f:
                # DictReader lee el CSV y convierte cada fila en un diccionario,
                # asumiendo que la primera fila del archivo contiene las claves (cabeceras).
                reader = csv.DictReader(f)
                
                for row in reader:
                    self._crear_task(row, source)
                    count += 1
        except FileNotFoundError as e:
            self.stderr.write(self.style.ERROR(f"Error importando {path}: {e}"))
        return count

    def _import_xml(self, path, source):
        count = 0
        try:
            # Parseamos (analizamos) la estructura del archivo XML en memoria.
            tree = ET.parse(path)
            
            # getroot() obtiene la etiqueta principal. findall("task") busca todas las etiquetas <task>.
            for task_el in tree.getroot().findall("task"):
                # Extraemos el texto de cada subetiqueta y armamos un diccionario
                # para que tenga la misma estructura que manejamos en el JSON o CSV.
                item = {
                    "title": task_el.find("title").text,
                    "priority": task_el.find("priority").text,
                    "status": task_el.find("status").text,
                }
                self._crear_task(item, source)
                count += 1
                
        # Atrapamos errores si el archivo no existe o el XML está corrupto (ParseError).
        except (FileNotFoundError, ET.ParseError) as e:
            self.stderr.write(self.style.ERROR(f"Error importando {path}: {e}"))
        return count

    def _crear_task(self, item, source):
        # Validación sencilla: si el diccionario no tiene título, informamos el error y lo ignoramos.
        if not item.get("title"):
            self.stderr.write(self.style.WARNING("Item sin título, se ignora"))
            return
        
        # Task.objects.create(...) es la forma en que el ORM de Django crea e inserta
        # una nueva fila en la tabla Task de la base de datos, sin tener que escribir SQL manual.
        Task.objects.create(
            title=item["title"],
            # Usamos el método .get("clave", "valor_por_defecto") de los diccionarios. 
            # Si el proveedor no envió 'priority' o 'status', se asigna 'media' y 'pendiente'.
            priority=item.get("priority", "media"),
            status=item.get("status", "pendiente"),
            source=source,
        )
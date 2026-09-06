from django.db import models
 
 
class Project(models.Model):
    name = models.CharField(max_length=150)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
 
    def __str__(self):
        return self.name
 
 
class Tag(models.Model):
    name = models.CharField(max_length=50, unique=True)
 
    def __str__(self):
        return self.name
 
 
class Task(models.Model):
    PRIORITY_CHOICES = [("baja", "Baja"), ("media", "Media"), ("alta", "Alta")]
    STATUS_CHOICES = [
        ("pendiente", "Pendiente"),
        ("en_progreso", "En progreso"),
        ("completada", "Completada"),
    ]
 
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="tasks")
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default="media")
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default="pendiente")
    due_date = models.DateField(null=True, blank=True)
    tags = models.ManyToManyField(Tag, blank=True, related_name="tasks")
    created_at = models.DateTimeField(auto_now_add=True)
 
    def __str__(self):
        return f"{self.title} ({self.project.name})"
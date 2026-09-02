from django.db import models

# Create your models here.
class Task(models.Model):
    PRIORITY_CHOICES = [("baja", "Baja"), ("media", "Media"), ("alta", "Alta")]
    STATUS_CHOICES = [
        ("pendiente", "Pendiente"),
        ("en_progreso", "En progreso"),
        ("completada", "Completada"),
    ]
 
    title = models.CharField(max_length=200)
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default="media")
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default="pendiente")
    source = models.CharField(max_length=50, blank=True)  # de qué proveedor vino
    created_at = models.DateTimeField(auto_now_add=True)
 
    def __str__(self):
        return self.title
    
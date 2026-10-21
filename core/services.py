import requests
from django.core.cache import cache

from django.utils import timezone
from rest_framework.exceptions import ValidationError
 
from .models import Task, Project, ProjectMembership
from .repositories import TaskRepository
 
 
class TaskService:
    @staticmethod
    def mark_completed(task: Task) -> Task:
        # Misma regla de negocio que TaskSerializer.validate (Clase 4)
        if not task.due_date:
            raise ValidationError(
                "No se puede marcar una tarea como completada sin fecha límite registrada."
            )
        task.status = "completada"
        task.save(update_fields=["status"])
        return task
 
    @staticmethod
    def tasks_overdue(queryset=None):
        if queryset is None:
            queryset = TaskRepository.get_queryset()
        today = timezone.now().date()
        return queryset.filter(due_date__lt=today).exclude(status="completada")

class HolidayService:
    API_URL = "https://date.nager.at/api/v3/PublicHolidays/{year}/AR"
 
    @classmethod
    def get_holidays(cls, year: int) -> list[str]:
        cache_key = f"holidays_{year}"
        cached = cache.get(cache_key)
        if cached is not None:
            return cached
        try:
            response = requests.get(cls.API_URL.format(year=year), timeout=5)
            response.raise_for_status()
            dates = [item["date"] for item in response.json()]
            cache.set(cache_key, dates, timeout=60 * 60 * 24)  # 24 horas
        except (requests.RequestException, ValueError, KeyError):
            dates = []
            cache.set(cache_key, dates, timeout=60 * 5)  # si falló, reintentamos en 5 minutos
        return dates
 
    @classmethod
    def is_holiday(cls, some_date) -> bool:
        return str(some_date) in cls.get_holidays(some_date.year)

class MembershipService:
    @staticmethod
    def is_member(user, project) -> bool:
        return ProjectMembership.objects.filter(project=project, user=user).exists()
 
    @staticmethod
    def is_admin(user, project) -> bool:
        return ProjectMembership.objects.filter(project=project, user=user, role="admin").exists()
 
    @staticmethod
    def projects_for(user):
        return Project.objects.filter(memberships__user=user).distinct().order_by("id")
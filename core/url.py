from django.urls import path
from . import views
 
urlpatterns = [
    path("estado/", views.health_check, name="health_check"),
    path("projects/", views.project_list, name="project_list"),
    path("tasks/", views.task_list, name="task_list"),
]
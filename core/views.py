from django.shortcuts import render

# Create your views here.
from django.http import JsonResponse

def health_check(request):
    return JsonResponse({"status": "ok", "service": "1era clase Python (Que Lio) API"})


from django.http import JsonResponse
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import Project, Task
from .serializers import ProjectSerializer, TaskSerializer


def health_check(request):
    return JsonResponse({"status": "ok", "service": "TaskFlow API"})


@api_view(["GET"])
def project_list(request):
    projects = Project.objects.all()
    serializer = ProjectSerializer(projects, many=True)
    return Response(serializer.data)


@api_view(["GET"])
def task_list(request):
     tasks = Task.objects.select_related("project").prefetch_related("tags").all()
     serializer = TaskSerializer(tasks, many=True)
     return Response(serializer.data)

from rest_framework import viewsets
from .models import Project, Task
from .serializers import ProjectSerializer, TaskSerializer
 
 
class ProjectViewSet(viewsets.ModelViewSet):
    queryset = Project.objects.all()
    serializer_class = ProjectSerializer
 
 
class TaskViewSet(viewsets.ModelViewSet):
    queryset = Task.objects.select_related("project").prefetch_related("tags").all()
    serializer_class = TaskSerializer
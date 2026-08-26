from django.urls import path
from . import views
 
urlpatterns = [
    path("estado/", views.health_check, name="health_check"),
]
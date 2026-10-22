from django.urls import path
from django.views.generic import TemplateView

urlpatterns = [
    # Una sola página: todo lo demás lo hace JavaScript hablando con /api/
    path("", TemplateView.as_view(template_name="frontend/index.html"), name="frontend"),
]

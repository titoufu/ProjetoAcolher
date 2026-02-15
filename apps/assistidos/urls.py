from django.urls import path
from . import views

app_name = "assistidos"

urlpatterns = [
    path("", views.assistido_list, name="list"),
]

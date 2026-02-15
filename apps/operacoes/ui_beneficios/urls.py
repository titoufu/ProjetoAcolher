# apps/operacoes/beneficios/urls.py
from django.urls import path
from . import views

app_name = "beneficios"

urlpatterns = [
    path("", views.beneficio_lista, name="beneficio_lista"),
    path("novo/", views.beneficio_create, name="beneficio_create"),
    path("<int:id>/", views.beneficio_detail, name="beneficio_detail"),
    path("<int:id>/editar/", views.beneficio_update, name="beneficio_update"),
    path("<int:id>/deletar/", views.beneficio_delete, name="beneficio_delete"),
]

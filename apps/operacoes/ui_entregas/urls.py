from django.urls import path
from . import views

app_name = "entregas"

urlpatterns = [
    path("", views.lote_lista, name="lote_lista"),
    path("novo/", views.lote_create, name="lote_create"),
    path("<int:id>/", views.lote_detail, name="lote_detail"),
    path("<int:id>/editar/", views.lote_update, name="lote_update"),
    path("<int:id>/deletar/", views.lote_delete, name="lote_delete"),     
]

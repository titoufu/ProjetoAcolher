from django.urls import path
from . import views

app_name = "assistidos"

urlpatterns = [
    path("", views.lista_assistidos, name="assistidos_lista"),
    path("novo/", views.assistido_create, name="assistido_create"),
    path("<uuid:id>/", views.assistido_detail, name="assistido_detail"),
    path("<uuid:id>/editar/", views.assistido_update, name="assistido_update"),
    path("<uuid:id>/deletar/", views.assistido_delete, name="assistido_delete"),
    
    path("<uuid:id>/beneficios/",views.assistido_beneficios,name="assistido_beneficios"),
    path("<uuid:id>/beneficios/atribuir/",views.assistido_beneficio_create,name="assistido_beneficio_create"),

    path("<uuid:id>/beneficios/<int:bid>/editar/", views.assistido_beneficio_update, name="assistido_beneficio_update"),
    path("<uuid:id>/beneficios/<int:bid>/encerrar/", views.assistido_beneficio_encerrar, name="assistido_beneficio_encerrar"),

]

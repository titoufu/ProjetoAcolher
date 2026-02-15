from django.urls import path
from . import views

app_name = "atribuicoes"

urlpatterns = [
    path("", views.atribuicoes_lista, name="atribuicoes_lista"),
    path("nova/", views.selecionar_assistido_para_atribuicao, name="atribuicao_nova"),
]
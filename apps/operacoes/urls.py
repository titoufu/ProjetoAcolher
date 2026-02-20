from django.urls import path, include
from . import views

urlpatterns = [
    path("assistidos/", include("apps.operacoes.ui_assistidos.urls")),
    path("beneficios/", include("apps.operacoes.ui_beneficios.urls")),
    path("atribuicoes/", include("apps.operacoes.ui_atribuicoes.urls")),
    path("entregas/", include("apps.operacoes.ui_entregas.urls")),

    # Mantém o app de consultas (todas as rotas existentes continuam funcionando)
    path("consultas/", include("apps.operacoes.consultas.urls")),

    # Home do módulo Operações (apenas UMA)
    path("", views.home_view, name="operacoes_home"),

    # Nova página "home" de consultas (não conflita com o include acima)
    path("consultas-home/", views.consultas_home, name="operacoes_consultas_home"),
]
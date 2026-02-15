from django.urls import path, include
from . import views

urlpatterns = [
    path("assistidos/", include("apps.operacoes.ui_assistidos.urls")),
    path("beneficios/", include("apps.operacoes.ui_beneficios.urls")),
    path("atribuicoes/", include("apps.operacoes.ui_atribuicoes.urls")),
    path("entregas/", include("apps.operacoes.entregas.urls")), 
    path("consultas/", include("apps.operacoes.consultas.urls")),
    path("", views.home_view, name="operacoes_home"),
]

from django.urls import path
from . import views

app_name = "consultas"

urlpatterns = [
    path("identificacao/", views.identificacao_lista, name="identificacao_lista"),
    path("identificacao/imprimir/", views.identificacao_print, name="identificacao_print"),

    # ✅ NOVO: Socioeconômico
    path("socioeconomico/", views.socioeconomico_lista, name="socioeconomico_lista"),
    path("socioeconomico/imprimir/", views.socioeconomico_print, name="socioeconomico_print"),
    
    path("saude/", views.saude_lista, name="saude_lista"),
    path("saude/imprimir/", views.saude_print, name="saude_print"),

    path("atribuicoes/", views.atribuicoes_consulta, name="atribuicoes_consulta"),
    path("atribuicoes/imprimir/", views.atribuicoes_consulta_print, name="atribuicoes_consulta_print"),

    path("beneficio/assistidos/",views.beneficio_assistidos_consulta,name="beneficio_assistidos_consulta",),
    path("beneficio/assistidos/imprimir/",views.beneficio_assistidos_print,name="beneficio_assistidos_print",),
    # ✅ NOVO: Entregas (Lotes)
    path("entregas/", views.entregas_lotes_lista, name="entregas_lotes_lista"),
    path("entregas/imprimir/", views.entregas_lotes_print, name="entregas_lotes_print"),
    
    # ✅ NOVO: Entregas (Detalhe do lote)
    path("entregas/lote/", views.entregas_lote_detalhe, name="entregas_lote_detalhe"),
    path("entregas/lote/imprimir/", views.entregas_lote_print, name="entregas_lote_print"),
    
    # ✅ NOVO: Entregas — Lista de Chamada (em branco)
    path("entregas/lote/chamada/",views.entregas_lote_chamada,name="entregas_lote_chamada",),
    path("entregas/lote/chamada/imprimir/",views.entregas_lote_chamada_print,name="entregas_lote_chamada_print",),


    path("entregas/assistido/",views.entregas_assistido_historico,name="entregas_assistido_historico",),
    path("entregas/assistido/imprimir/",views.entregas_assistido_historico_print,name="entregas_assistido_historico_print",),

    path("consultas/lotes/", views.consulta_lotes_resumo, name="consulta_lotes_resumo"),


    ]


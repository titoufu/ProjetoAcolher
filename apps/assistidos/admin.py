from django.contrib import admin
from .models import Assistido


@admin.register(Assistido)
class AssistidoAdmin(admin.ModelAdmin):
    # ==============================
    # LISTAGEM
    # ==============================
    list_display = (
        "nome",
        "cpf_formatado",
        "telefone",
        "status",
        "bairro",
        "cidade",
        "uf",
        "cep_formatado",
    )

    # ==============================
    # FILTROS E BUSCA
    # ==============================
    list_filter = (
        "status",
        "uf",
        "bairro",
        "cidade",
        "sit_trabalho",
        "faixa_renda",
        "tipo_moradia",
        "area_risco",
    )

    search_fields = (
        "nome",
        "cpf",
        "telefone",
        "bairro",
        "logradouro",
        "cidade",
    )

    ordering = ("nome",)

    # ==============================
    # SOMENTE LEITURA
    # ==============================
    readonly_fields = (
        "codigo",
        "criado_em",
        "data_inativacao",
        "endereco_resumo",
    )

    # ==============================
    # FORMULÁRIO (FIELDSETS)
    # ==============================
    fieldsets = (
        ("Identificação", {
            "fields": (
                "nome",
                "cpf",
                "data_nascimento",
                "telefone",
                "status",
                "motivo_inativacao",
            )
        }),

        ("Endereço", {
            "fields": (
                "logradouro",
                "numero",
                "complemento",
                "bairro",
                "cidade",
                "uf",
                "cep",
                "endereco_resumo",
            )
        }),

        ("Situação Socioeconômica", {
            "fields": (
                "sit_trabalho",
                "responsavel_renda",
                "faixa_renda",
                "tipo_moradia",
                "material_moradia",
                "area_risco",
                "sabe_ler_escrever",
                "escolaridade",
            )
        }),

        ("Condições de Saúde", {
            "fields": (
                "diabetes",
                "pressao_alta",
                "medic_uso_continuo",
                "doenca_permanente",
            )
        }),

        ("Programa", {
            "fields": (
                "data_inicio_apoio",
            ),
            
        }),

        ("Informações do Sistema", {
            "fields": (
                "codigo",
                "criado_em",
                "data_inativacao",
            )
        }),
    )

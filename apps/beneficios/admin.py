from django.contrib import admin
from .models import Beneficio, BeneficioAssistido,  LoteEntrega, ItemEntrega


class ItemEntregaInline(admin.TabularInline):
    model = ItemEntrega
    extra = 0
    fields = ("assistido_nome", "entregue")
    readonly_fields = ("assistido_nome",)

    def assistido_nome(self, obj):
        # obj.atribuicao -> BeneficioAssistido -> assistido -> nome
        return obj.atribuicao.assistido.nome

    assistido_nome.short_description = "Assistido"


@admin.register(Beneficio)
class BeneficioAdmin(admin.ModelAdmin):
    list_display = ("nome", "categoria", "periodicidade", "ativo")
    list_filter = ("categoria", "periodicidade", "ativo")
    search_fields = ("nome",)
    ordering = ("categoria", "nome")


@admin.register(BeneficioAssistido)
class BeneficioAssistidoAdmin(admin.ModelAdmin):
    list_display = ("assistido", "beneficio", "ativo", "criado_em")
    list_filter = ("ativo", "beneficio")
    search_fields = ("assistido__nome", "beneficio__nome")
    ordering = ("-criado_em",)

@admin.register(LoteEntrega)
class LoteEntregaAdmin(admin.ModelAdmin):
    list_display = ("id", "beneficio", "data_entrega", "criado_em")
    list_filter = ("beneficio", "data_entrega")
    search_fields = ("beneficio__nome",)
    date_hierarchy = "data_entrega"
    inlines = [ItemEntregaInline]

    def save_model(self, request, obj, form, change):
        # 1) Salva o lote primeiro (precisa do obj.id)
        super().save_model(request, obj, form, change)

        # 2) Se já existem itens, não gera de novo
        if obj.itens.exists():
            return

        # 3) Busca atribuições aptas (ativo=True) para o benefício do lote
        atribuicoes = (
            BeneficioAssistido.objects
            .select_related("assistido", "beneficio")
            .filter(beneficio=obj.beneficio, ativo=True)
        )

        # 4) Cria os itens do lote (1 por atribuição)
        itens = [ItemEntrega(lote=obj, atribuicao=a) for a in atribuicoes]

        # 5) Grava em lote (e evita conflito se algo já existir)
        ItemEntrega.objects.bulk_create(itens, ignore_conflicts=True)


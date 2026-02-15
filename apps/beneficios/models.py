from django.db import models
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.db.models import Q


class CategoriaBeneficio(models.TextChoices):
    ALIMENTACAO = "ALIMENTACAO", "Alimentação"
    SAUDE = "SAUDE", "Saúde"
    VESTUARIO = "VESTUARIO", "Vestuário"
    OUTROS = "OUTROS", "Outros"


class PeriodicidadeBeneficio(models.TextChoices):
    SEMANAL = "SEMANAL", "Semanal"
    MENSAL = "MENSAL", "Mensal"
    OCASIONAL = "OCASIONAL", "Ocasional"


class Beneficio(models.Model):
    """
    Benefício (Catálogo)

    Representa um "tipo de benefício" disponível no sistema.
    Ex.: Cesta Básica Mensal, Hortifruti Semanal, Consulta Cardiologista etc.

    Importante: Benefício existe independentemente de Assistido.
    A atribuição (Assistido receber Benefício) será feita por um model intermediário
    no próximo passo.
    """

    nome = models.CharField(max_length=120, unique=True)

    categoria = models.CharField(
        max_length=20,
        choices=CategoriaBeneficio.choices,
    )

    periodicidade = models.CharField(
        max_length=20,
        choices=PeriodicidadeBeneficio.choices,
    )

    ativo = models.BooleanField(
        default=True,
        help_text="Permite desativar um benefício sem apagá-lo.",
    )

    class Meta:
        ordering = ["categoria", "nome"]

    def __str__(self) -> str:
        return self.nome
    
class BeneficioAssistido(models.Model):
    """
    Entidade intermediária (Atribuição)

    Representa o ato de atribuir um Benefício (catálogo) a um Assistido.
    ✅ Um assistido pode ter vários ciclos do mesmo benefício ao longo do tempo,
       mas não pode ter dois ciclos ATIVOS simultaneamente.
    """

    assistido = models.ForeignKey(
        "assistidos.Assistido",
        on_delete=models.PROTECT,
        related_name="beneficios_atribuidos",
    )

    beneficio = models.ForeignKey(
        "Beneficio",
        on_delete=models.PROTECT,
        related_name="assistidos_atribuidos",
    )

    ativo = models.BooleanField(
        default=True,
        help_text="Permite encerrar a atribuição sem apagar histórico.",
    )

    data_inicio = models.DateField(default=timezone.localdate)
    data_termino = models.DateField(null=True, blank=True)

    criado_em = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ["-criado_em"]
        constraints = [
            models.UniqueConstraint(
                fields=["assistido", "beneficio"],
                condition=Q(ativo=True),
                name="uniq_assistido_beneficio_ativo",
            )
        ]

    def save(self, *args, **kwargs):
        """
        Mantém 'ativo' coerente com a vigência:
        - Se ainda não começou (data_inicio > hoje): inativo
        - Se terminou (data_termino preenchida e < hoje): inativo
        - Caso contrário: ativo
        """
        hoje = timezone.localdate()

        vigente = True

        if self.data_inicio and self.data_inicio > hoje:
            vigente = False

        if self.data_termino and self.data_termino <= hoje:
            vigente = False

        self.ativo = vigente

        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return f"{self.assistido.nome} → {self.beneficio.nome}"


def clean(self):
    super().clean()

    # 1) Datas: término não pode ser < início
    if self.data_termino and self.data_inicio and self.data_termino < self.data_inicio:
        raise ValidationError({
            "data_termino": "A data de término não pode ser anterior à data de início."
        })

    # 2) Consistência básica: se está ENCERRADA, precisa ter data_termino
    if self.ativo is False and not self.data_termino:
        raise ValidationError({
            "data_termino": "Informe a data de término ao encerrar a atribuição."
        })

    # 3) Regras de negócio: só aplicam quando a atribuição está ATIVA
    # (histórico pode ser ajustado mesmo que assistido/benefício estejam inativos hoje)
    if self.ativo:

        # 3.1) Assistido precisa estar ATIVO para receber benefício ATIVO
        if self.assistido and not self.assistido.is_ativo:
            raise ValidationError({
                "assistido": "Somente assistidos ATIVOS podem receber benefícios."
            })

        # 3.2) Benefício precisa estar ATIVO para ser atribuído (exceto manter o mesmo na edição)
        if self.beneficio and not self.beneficio.ativo:
            if self.pk:
                beneficio_original_id = (
                    BeneficioAssistido.objects
                    .filter(pk=self.pk)
                    .values_list("beneficio_id", flat=True)
                    .first()
                )
                # se está trocando o benefício por um inativo, bloquear
                if beneficio_original_id != self.beneficio_id:
                    raise ValidationError({
                        "beneficio": "Somente benefícios ATIVOS podem ser atribuídos."
                    })
                # se manteve o mesmo benefício (mesmo inativo), deixa passar (edição de histórico)
            else:
                # novo registro com benefício inativo
                raise ValidationError({
                    "beneficio": "Somente benefícios ATIVOS podem ser atribuídos."
                })

        # 3.3) Unicidade lógica: não pode haver outro ciclo ATIVO do mesmo benefício
        if self.assistido_id and self.beneficio_id:
            qs = BeneficioAssistido.objects.filter(
                assistido_id=self.assistido_id,
                beneficio_id=self.beneficio_id,
                ativo=True,
            )
            if self.pk:
                qs = qs.exclude(pk=self.pk)

            if qs.exists():
                raise ValidationError({
                    "beneficio": "Este benefício já está ATIVO para este assistido. Encerre o ciclo atual para conceder novamente."
                })

class LoteEntrega(models.Model):
    beneficio = models.ForeignKey(
        "beneficios.Beneficio",
        on_delete=models.PROTECT,
        related_name="lotes_entrega",
    )
    data_entrega = models.DateField()
    criado_em = models.DateTimeField(default=timezone.now)

    class Meta:
        unique_together = ("beneficio", "data_entrega")
        ordering = ("-data_entrega", "-id")
        verbose_name = "Lote de Entrega"
        verbose_name_plural = "Lotes de Entrega"

    def __str__(self):
        return f"{self.beneficio} - {self.data_entrega.strftime('%d/%m/%Y')}"

class ItemEntrega(models.Model):
    lote = models.ForeignKey(
        LoteEntrega,
        on_delete=models.CASCADE,
        related_name="itens",
    )
    atribuicao = models.ForeignKey(
        "beneficios.BeneficioAssistido",
        on_delete=models.PROTECT,
        related_name="entregas",
    )
    entregue = models.BooleanField(default=False)

    class Meta:
        unique_together = ("lote", "atribuicao")
        ordering = ("atribuicao__assistido__nome",)
        verbose_name = "Item de Entrega"
        verbose_name_plural = "Itens de Entrega"

    def __str__(self):
        status = "Entregue" if self.entregue else "Pendente"
        return f"{self.lote} - {self.atribuicao} ({status})"
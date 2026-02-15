from __future__ import annotations

import secrets
import uuid
from datetime import date

from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone


# =============================================================================
# FUNÇÕES AUXILIARES
# =============================================================================

def normalizar_cep(valor: str | None) -> str:
    if not valor:
        return ""
    return "".join(c for c in valor if c.isdigit())


def normalizar_cpf(valor: str | None) -> str:
    if not valor:
        return ""
    return "".join(c for c in valor if c.isdigit())


def cpf_valido(cpf: str) -> bool:
    cpf = normalizar_cpf(cpf)

    if len(cpf) != 11:
        return False
    if cpf == cpf[0] * 11:
        return False

    def calc(base, pesos):
        soma = sum(int(d) * p for d, p in zip(base, pesos))
        resto = soma % 11
        return "0" if resto < 2 else str(11 - resto)

    d1 = calc(cpf[:9], range(10, 1, -1))
    d2 = calc(cpf[:9] + d1, range(11, 1, -1))
    return cpf[-2:] == d1 + d2


# =============================================================================
# CHOICES
# =============================================================================

class StatusCadastro(models.TextChoices):
    ATIVO = "ATIVO", "Ativo"
    INATIVO = "INATIVO", "Inativo"


class TriSimNao(models.TextChoices):
    SIM = "SIM", "Sim"
    NAO = "NAO", "Não"
    NAO_INFORMADO = "NAO_INFORMADO", "Não informado"


class SituacaoTrabalho(models.TextChoices):
    EMPREGADO = "EMPREGADO", "Empregado"
    DESEMPREGADO = "DESEMPREGADO", "Desempregado"
    AUTONOMO = "AUTONOMO", "Autônomo"
    APOSENTADO = "APOSENTADO", "Aposentado"
    NAO_INFORMADO = "NAO_INFORMADO", "Não informado"


class ResponsavelRenda(models.TextChoices):
    ASSISTIDO = "ASSISTIDO", "Assistido"
    CONJUGE = "CONJUGE", "Cônjuge"
    OUTRO = "OUTRO", "Outro"
    NAO_INFORMADO = "NAO_INFORMADO", "Não informado"


class FaixaRenda(models.TextChoices):
    ATE_1_SM = "ATE_1_SM", "Até 1 salário mínimo"
    DE_1_A_2_SM = "DE_1_A_2_SM", "De 1 a 2 salários mínimos"
    ACIMA_2_SM = "ACIMA_2_SM", "Acima de 2 salários mínimos"
    NAO_INFORMADO = "NAO_INFORMADO", "Não informado"


class TipoMoradia(models.TextChoices):
    PROPRIA = "PROPRIA", "Própria"
    ALUGADA = "ALUGADA", "Alugada"
    CEDIDA = "CEDIDA", "Cedida"
    NAO_INFORMADO = "NAO_INFORMADO", "Não informado"


class MaterialMoradia(models.TextChoices):
    ALVENARIA = "ALVENARIA", "Alvenaria"
    MADEIRA = "MADEIRA", "Madeira"
    MISTA = "MISTA", "Mista"
    NAO_INFORMADO = "NAO_INFORMADO", "Não informado"


class Escolaridade(models.TextChoices):
    FUNDAMENTAL = "FUNDAMENTAL", "Fundamental"
    MEDIO = "MEDIO", "Médio"
    SUPERIOR = "SUPERIOR", "Superior"
    NAO_INFORMADO = "NAO_INFORMADO", "Não informado"


# =============================================================================
# MODEL
# =============================================================================

class Assistido(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    codigo = models.CharField(max_length=30, unique=True, blank=True, null=True)

    nome = models.CharField(max_length=120)
    cpf = models.CharField(max_length=11, blank=True, null=True, unique=True,verbose_name="CPF")
    data_nascimento = models.DateField(blank=True, null=True)
    telefone = models.CharField(max_length=30, blank=True)

    # Endereço
    logradouro = models.CharField(max_length=120, blank=True)
    numero = models.CharField(max_length=20, blank=True)
    complemento = models.CharField(max_length=80, blank=True)
    bairro = models.CharField(max_length=80, blank=True)
    cidade = models.CharField(max_length=80, blank=True)
    uf = models.CharField(max_length=2, blank=True,verbose_name="UF")
    cep = models.CharField(max_length=9, blank=True,verbose_name="CEP")

    # Socioeconômico
    sit_trabalho = models.CharField(
        max_length=20, choices=SituacaoTrabalho.choices,
        default=SituacaoTrabalho.NAO_INFORMADO
    )
    responsavel_renda = models.CharField(
        max_length=20, choices=ResponsavelRenda.choices,
        default=ResponsavelRenda.NAO_INFORMADO
    )
    faixa_renda = models.CharField(
        max_length=20, choices=FaixaRenda.choices,
        default=FaixaRenda.NAO_INFORMADO
    )
    tipo_moradia = models.CharField(
        max_length=20, choices=TipoMoradia.choices,
        default=TipoMoradia.NAO_INFORMADO
    )
    material_moradia = models.CharField(
        max_length=20, choices=MaterialMoradia.choices,
        default=MaterialMoradia.NAO_INFORMADO
    )
    area_risco = models.CharField(
        max_length=20, choices=TriSimNao.choices,
        default=TriSimNao.NAO_INFORMADO
    )
    sabe_ler_escrever = models.CharField(
        max_length=20, choices=TriSimNao.choices,
        default=TriSimNao.NAO_INFORMADO
    )
    escolaridade = models.CharField(
        max_length=30, choices=Escolaridade.choices,
        default=Escolaridade.NAO_INFORMADO
    )

    # Saúde
    diabetes = models.CharField(max_length=20, choices=TriSimNao.choices, default=TriSimNao.NAO_INFORMADO)
    pressao_alta = models.CharField(max_length=20, choices=TriSimNao.choices, default=TriSimNao.NAO_INFORMADO)
    medic_uso_continuo = models.CharField(max_length=20, choices=TriSimNao.choices, default=TriSimNao.NAO_INFORMADO)
    doenca_permanente = models.CharField(max_length=20, choices=TriSimNao.choices, default=TriSimNao.NAO_INFORMADO)

    # Apoio
    data_inicio_apoio = models.DateField(blank=True, null=True,verbose_name="Ingresso no Programa")

    # Status
    status = models.CharField(max_length=10, choices=StatusCadastro.choices, default=StatusCadastro.ATIVO)
    data_inativacao = models.DateField(blank=True, null=True)
    motivo_inativacao = models.CharField(max_length=200, blank=True)

    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["nome"]

    def __str__(self):
        return self.nome

    # =========================
    # PROPERTIES
    # =========================

    @property
    def idade(self):
        if not self.data_nascimento:
            return None
        hoje = date.today()
        idade = hoje.year - self.data_nascimento.year
        if (hoje.month, hoje.day) < (self.data_nascimento.month, self.data_nascimento.day):
            idade -= 1
        return idade

    @property
    def cpf_formatado(self):
        if not self.cpf or len(self.cpf) != 11:
            return ""
        return f"{self.cpf[:3]}.{self.cpf[3:6]}.{self.cpf[6:9]}-{self.cpf[9:]}"

    @property
    def cep_formatado(self):
        cep = normalizar_cep(self.cep)
        if len(cep) != 8:
            return self.cep
        return f"{cep[:5]}-{cep[5:]}"

    @property
    def endereco_resumo(self):
        partes = []

        if self.logradouro:
            log = self.logradouro.title()
            if self.numero:
                log = f"{log}, {self.numero}"
            partes.append(log)

        if self.cep:
            partes.append(f"CEP {self.cep_formatado}")

        return " • ".join(partes)
    
    @property
    def telefone_formatado(self):
        tel = "".join(c for c in (self.telefone or "") if c.isdigit())

        if len(tel) == 10:  # (DD) XXXX-XXXX
            return f"({tel[:2]}) {tel[2:6]}-{tel[6:]}"
        if len(tel) == 11:  # (DD) XXXXX-XXXX
            return f"({tel[:2]}) {tel[2:7]}-{tel[7:]}"

        return self.telefone or ""
    @property
    def is_ativo(self) -> bool:
        return self.status == "ATIVO"


    # =========================
    # CLEAN / SAVE
    # =========================

    def clean(self):
        if self.cep and len(normalizar_cep(self.cep)) != 8:
            raise ValidationError({"cep": "CEP deve conter 8 dígitos."})
        if self.cpf and not cpf_valido(self.cpf):
            raise ValidationError({"cpf": "CPF inválido."})

    def save(self, *args, **kwargs):
        if not self.codigo:
            hoje = timezone.localdate().strftime("%Y%m%d")
            while True:
                sufixo = secrets.token_hex(2).upper()
                codigo = f"A-{hoje}-{sufixo}"
                if not Assistido.objects.filter(codigo=codigo).exists():
                    self.codigo = codigo
                    break

        if self.cpf:
            self.cpf = normalizar_cpf(self.cpf)
        else:
            self.cpf = None

        if self.cep:
            self.cep = normalizar_cep(self.cep)

        if self.status == StatusCadastro.INATIVO and not self.data_inativacao:
            self.data_inativacao = timezone.localdate()
        if self.status == StatusCadastro.ATIVO:
            self.data_inativacao = None

        super().save(*args, **kwargs)

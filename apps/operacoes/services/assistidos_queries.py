# apps/operacoes/services/assistidos_queries.py
from __future__ import annotations

from typing import Set
from django.db.models import Q, QuerySet

from apps.assistidos.models import Assistido

ALLOWED_STATUS: Set[str] = {"ATIVO", "INATIVO"}


def _filtro_texto(q: str) -> Q:
    q = (q or "").strip()
    if not q:
        return Q()
    return Q(nome__icontains=q) | Q(cpf__icontains=q) | Q(telefone__icontains=q)


def _filtro_status(status: str) -> Q:
    status = (status or "").strip().upper()
    if status in ALLOWED_STATUS:
        return Q(status=status)
    return Q()


def _safe_order(raw: str, allowed: set[str], default: str) -> str:
    raw = (raw or "").strip() or default
    campo = raw.lstrip("-")
    return raw if campo in allowed else default


def assistidos_identificacao_qs(
    *,
    q: str = "",
    status: str = "",
    logradouro: str = "",
    cep: str = "",
    order: str = "nome",
) -> QuerySet[Assistido]:
    qs = Assistido.objects.all()
    qs = qs.filter(_filtro_texto(q))
    qs = qs.filter(_filtro_status(status))

    logradouro = (logradouro or "").strip()
    if logradouro:
        qs = qs.filter(logradouro__icontains=logradouro)

    cep = (cep or "").strip()
    if cep:
        cep_clean = cep.replace("-", "").strip()
        qs = qs.filter(cep__icontains=cep_clean)

    allowed = {"nome", "status", "cep", "logradouro"}
    return qs.order_by(_safe_order(order, allowed, "nome"))


def assistidos_socioeconomico_qs(
    *,
    q: str = "",
    status: str = "",
    sit_trabalho: str = "",
    faixa_renda: str = "",
    tipo_moradia: str = "",
    area_risco: str = "",
    escolaridade: str = "",
    order: str = "nome",
) -> QuerySet[Assistido]:
    qs = Assistido.objects.all()
    qs = qs.filter(_filtro_texto(q))
    qs = qs.filter(_filtro_status(status))

    if sit_trabalho:
        qs = qs.filter(sit_trabalho=sit_trabalho)
    if faixa_renda:
        qs = qs.filter(faixa_renda=faixa_renda)
    if tipo_moradia:
        qs = qs.filter(tipo_moradia=tipo_moradia)
    if area_risco:
        qs = qs.filter(area_risco=area_risco)
    if escolaridade:
        qs = qs.filter(escolaridade=escolaridade)

    allowed = {"nome", "sit_trabalho", "faixa_renda", "tipo_moradia", "escolaridade"}
    return qs.order_by(_safe_order(order, allowed, "nome"))


def assistidos_saude_qs(
    *,
    q: str = "",
    status: str = "",
    diabetes: str = "",
    pressao_alta: str = "",
    medic_uso_continuo: str = "",
    doenca_permanente: str = "",
    order: str = "nome",
) -> QuerySet[Assistido]:
    qs = Assistido.objects.all()
    qs = qs.filter(_filtro_texto(q))
    qs = qs.filter(_filtro_status(status))

    if diabetes:
        qs = qs.filter(diabetes=diabetes)
    if pressao_alta:
        qs = qs.filter(pressao_alta=pressao_alta)
    if medic_uso_continuo:
        qs = qs.filter(medic_uso_continuo=medic_uso_continuo)
    if doenca_permanente:
        qs = qs.filter(doenca_permanente=doenca_permanente)

    allowed = {"nome", "diabetes", "pressao_alta", "medic_uso_continuo", "doenca_permanente"}
    return qs.order_by(_safe_order(order, allowed, "nome"))


def assistidos_choices_para_filtros():
    """
    Centraliza CHOICES usados nos filtros dos templates.
    Você injeta isso no contexto com **assistidos_choices_para_filtros()
    """
    return {
        "choices_sit_trabalho": Assistido._meta.get_field("sit_trabalho").choices,
        "choices_faixa_renda": Assistido._meta.get_field("faixa_renda").choices,
        "choices_tipo_moradia": Assistido._meta.get_field("tipo_moradia").choices,
        "choices_area_risco": Assistido._meta.get_field("area_risco").choices,
        "choices_escolaridade": Assistido._meta.get_field("escolaridade").choices,
        "choices_diabetes": Assistido._meta.get_field("diabetes").choices,
        "choices_pressao_alta": Assistido._meta.get_field("pressao_alta").choices,
        "choices_medic_uso_continuo": Assistido._meta.get_field("medic_uso_continuo").choices,
        "choices_doenca_permanente": Assistido._meta.get_field("doenca_permanente").choices,
    }

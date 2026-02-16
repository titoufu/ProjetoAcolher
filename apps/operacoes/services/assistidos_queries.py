# apps/operacoes/services/assistidos_queries.py
from __future__ import annotations

from django.db.models import Q
from apps.assistidos.models import Assistido


# =========================
# Helpers internos
# =========================

def _base_qs():
    """QuerySet base para consultas de Assistidos."""
    return Assistido.objects.all()


def _apply_q_search(qs, q: str):
    """
    Busca textual padrão (nome/cpf/telefone).
    Mantemos igual ao que você já usa nas consultas.
    """
    q = (q or "").strip()
    if not q:
        return qs

    return qs.filter(
        Q(nome__icontains=q)
        | Q(cpf__icontains=q)
        | Q(telefone__icontains=q)
    )


def _apply_status_filter(qs, status: str):
    """Filtro padrão de status (ATIVO/INATIVO)."""
    status = (status or "").strip()
    if status in {"ATIVO", "INATIVO"}:
        return qs.filter(status=status)
    return qs


def _normalize_cep(cep: str) -> str:
    """Normaliza CEP digitado (remove hífen e espaços)."""
    return (cep or "").replace("-", "").strip()


# =========================
# Consultas públicas
# =========================

def assistidos_identificacao_qs(
    *,
    q: str = "",
    status: str = "",
    logradouro: str = "",
    cep: str = "",
    order_by: str = "nome",
):
    """
    Consulta: Identificação e Endereço (lista e impressão usam a mesma função)
    """
    qs = _base_qs()
    qs = _apply_q_search(qs, q)
    qs = _apply_status_filter(qs, status)

    logradouro = (logradouro or "").strip()
    if logradouro:
        qs = qs.filter(logradouro__icontains=logradouro)

    cep_clean = _normalize_cep(cep)
    if cep_clean:
        qs = qs.filter(cep__icontains=cep_clean)

    return qs.order_by(order_by)


def assistidos_saude_qs(
    *,
    q: str = "",
    status: str = "",
    diabetes: str = "",
    pressao_alta: str = "",
    medic_uso_continuo: str = "",
    doenca_permanente: str = "",
    order_by: str = "nome",
):
    """
    Consulta: Condições de Saúde (lista e impressão usam a mesma função)
    """
    qs = _base_qs()
    qs = _apply_q_search(qs, q)
    qs = _apply_status_filter(qs, status)

    diabetes = (diabetes or "").strip()
    pressao_alta = (pressao_alta or "").strip()
    medic_uso_continuo = (medic_uso_continuo or "").strip()
    doenca_permanente = (doenca_permanente or "").strip()

    if diabetes:
        qs = qs.filter(diabetes=diabetes)
    if pressao_alta:
        qs = qs.filter(pressao_alta=pressao_alta)
    if medic_uso_continuo:
        qs = qs.filter(medic_uso_continuo=medic_uso_continuo)
    if doenca_permanente:
        qs = qs.filter(doenca_permanente=doenca_permanente)

    return qs.order_by(order_by)


def assistidos_socioeconomico_qs(
    *,
    q: str = "",
    status: str = "",
    sit_trabalho: str = "",
    faixa_renda: str = "",
    tipo_moradia: str = "",
    escolaridade: str = "",
    area_risco: str = "",
    order_by: str = "nome",
):
    """
    Consulta: Situação Socioeconômica (lista e impressão usam a mesma função)
    """
    qs = _base_qs()
    qs = _apply_q_search(qs, q)
    qs = _apply_status_filter(qs, status)

    sit_trabalho = (sit_trabalho or "").strip()
    faixa_renda = (faixa_renda or "").strip()
    tipo_moradia = (tipo_moradia or "").strip()
    escolaridade = (escolaridade or "").strip()
    area_risco = (area_risco or "").strip()

    if sit_trabalho:
        qs = qs.filter(sit_trabalho=sit_trabalho)
    if faixa_renda:
        qs = qs.filter(faixa_renda=faixa_renda)
    if tipo_moradia:
        qs = qs.filter(tipo_moradia=tipo_moradia)
    if escolaridade:
        qs = qs.filter(escolaridade=escolaridade)
    if area_risco:
        qs = qs.filter(area_risco=area_risco)

    return qs.order_by(order_by)

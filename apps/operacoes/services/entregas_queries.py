  # apps/operacoes/services/entregas_queries.py
from __future__ import annotations

from datetime import date
from typing import Optional, Tuple

from django.db.models import Count, Q

from apps.beneficios.models import LoteEntrega, ItemEntrega, Beneficio, BeneficioAssistido
from apps.assistidos.models import Assistido


def _parse_date(s: str) -> Optional[date]:
    """Aceita 'YYYY-MM-DD'. Retorna None se vazio/ inválido."""
    s = (s or "").strip()
    if not s:
        return None
    try:
        return date.fromisoformat(s)
    except ValueError:
        return None


def _normalize_status(status: str) -> str:
    status = (status or "todos").strip().lower()
    if status not in {"todos", "entregue", "pendente"}:
        status = "todos"
    return status


def lotes_com_resumo(
    *,
    q: str = "",
    data_ini: str = "",
    data_fim: str = "",
    beneficio_id: str = "",
):
    """
    QuerySet de LoteEntrega com anotações:
      - total_itens
      - entregues
      - pendentes
    e filtros opcionais por:
      - benefício
      - intervalo de data
      - texto (nome do benefício ou ID do lote)
    """
    qs = LoteEntrega.objects.select_related("beneficio")

    di = _parse_date(data_ini)
    df = _parse_date(data_fim)
    if di:
        qs = qs.filter(data_entrega__gte=di)
    if df:
        qs = qs.filter(data_entrega__lte=df)

    if beneficio_id:
        try:
            bid = int(beneficio_id)
            qs = qs.filter(beneficio_id=bid)
        except ValueError:
            pass

    q = (q or "").strip()
    if q:
        # busca por: nome do benefício ou ID do lote
        cond = Q(beneficio__nome__icontains=q)
        if q.isdigit():
            cond |= Q(id=int(q))
        qs = qs.filter(cond)

    qs = qs.annotate(
        total_itens=Count("itens", distinct=True),
        entregues=Count("itens", filter=Q(itens__entregue=True), distinct=True),
        pendentes=Count("itens", filter=Q(itens__entregue=False), distinct=True),
    ).order_by("-data_entrega", "-id")

    return qs


def historico_itens_por_assistido(
    *,
    q: str = "",
    data_ini: str = "",
    data_fim: str = "",
    beneficio_id: str = "",
    status: str = "todos",
):
    """
    QuerySet de ItemEntrega (com lote/benefício/assistido via atribuicao) com filtros:
      - texto: nome do assistido
      - intervalo de datas no lote
      - benefício do lote
      - status (todos/entregue/pendente)
    """
    status = _normalize_status(status)

    qs = (
        ItemEntrega.objects
        .select_related("lote", "lote__beneficio", "atribuicao", "atribuicao__assistido")
    )

    di = _parse_date(data_ini)
    df = _parse_date(data_fim)
    if di:
        qs = qs.filter(lote__data_entrega__gte=di)
    if df:
        qs = qs.filter(lote__data_entrega__lte=df)

    if beneficio_id:
        try:
            bid = int(beneficio_id)
            qs = qs.filter(lote__beneficio_id=bid)
        except ValueError:
            pass

    q = (q or "").strip()
    if q:
        qs = qs.filter(
            Q(atribuicao__assistido__nome__icontains=q)
            | Q(atribuicao__assistido__cpf__icontains=q)
            | Q(atribuicao__assistido__telefone__icontains=q)
        )

    if status == "entregue":
        qs = qs.filter(entregue=True)
    elif status == "pendente":
        qs = qs.filter(entregue=False)

    # ordena por data do lote desc, depois assistido
    qs = qs.order_by("-lote__data_entrega", "atribuicao__assistido__nome", "-lote_id", "-id")
    return qs


def opcoes_beneficios():
    """Benefícios ordenados para preencher <select> de filtro."""
    return Beneficio.objects.order_by("nome", "id")

def _normalize_status(status: str) -> str:
    status = (status or "todos").strip().lower()
    mapa = {
        "todos": "todos",
        "entregue": "entregue",
        "entregues": "entregue",
        "pendente": "pendente",
        "pendentes": "pendente",
    }
    return mapa.get(status, "todos")

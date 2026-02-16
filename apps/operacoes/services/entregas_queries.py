# apps/operacoes/services/entregas_queries.py
from __future__ import annotations

from datetime import date
from typing import Optional, Tuple

from django.db.models import Count, Q, QuerySet
from django.shortcuts import get_object_or_404

from apps.beneficios.models import Beneficio, ItemEntrega, LoteEntrega


def _parse_date(s: str) -> Optional[date]:
    s = (s or "").strip()
    if not s:
        return None
    try:
        return date.fromisoformat(s)
    except ValueError:
        return None


def _normalize_status(status: str) -> str:
    """
    Aceita: todos / entregue(s) / pendente(s)
    Normaliza para: todos / entregue / pendente
    """
    status = (status or "todos").strip().lower()
    mapa = {
        "todos": "todos",
        "entregue": "entregue",
        "entregues": "entregue",
        "pendente": "pendente",
        "pendentes": "pendente",
    }
    return mapa.get(status, "todos")


def opcoes_beneficios() -> QuerySet[Beneficio]:
    return Beneficio.objects.order_by("nome", "id")


def lotes_com_resumo(
    *,
    data_ini: str = "",
    data_fim: str = "",
    beneficio_id: str = "",
    order_by: str = "-data_entrega",
) -> QuerySet[LoteEntrega]:
    """
    Retorna LoteEntrega com:
      - total (Count itens)
      - entregues (Count itens entregues)
      - pendentes (Count itens pendentes)
    """
    qs = LoteEntrega.objects.select_related("beneficio")

    di = _parse_date(data_ini)
    df = _parse_date(data_fim)
    if di:
        qs = qs.filter(data_entrega__gte=di)
    if df:
        qs = qs.filter(data_entrega__lte=df)

    beneficio_id = (beneficio_id or "").strip()
    if beneficio_id:
        try:
            qs = qs.filter(beneficio_id=int(beneficio_id))
        except ValueError:
            pass

    qs = qs.annotate(
        total=Count("itens", distinct=True),
        entregues=Count("itens", filter=Q(itens__entregue=True), distinct=True),
        pendentes=Count("itens", filter=Q(itens__entregue=False), distinct=True),
    )

    # fallback seguro de ordenação
    allowed = {
        "data_entrega", "-data_entrega",
        "beneficio__nome", "-beneficio__nome",
        "total", "-total",
        "entregues", "-entregues",
        "pendentes", "-pendentes",
    }
    order = order_by if order_by in allowed else "-data_entrega"
    return qs.order_by(order, "-id")


def itens_do_lote(
    *,
    lote_id: str,
    order_by: str = "atribuicao__assistido__nome",
) -> Tuple[LoteEntrega, QuerySet[ItemEntrega], QuerySet[ItemEntrega], QuerySet[ItemEntrega]]:
    """
    Retorna:
      (lote, itens_qs, entregues_qs, pendentes_qs)
    """
    lote_id = (lote_id or "").strip()
    lote_int = int(lote_id)  # se vier inválido, explode aqui (ok: view já garante fluxo)
    lote = get_object_or_404(LoteEntrega.objects.select_related("beneficio"), id=lote_int)

    allowed = {
        "atribuicao__assistido__nome",
        "-atribuicao__assistido__nome",
        "entregue",
        "-entregue",
    }
    order = order_by if order_by in allowed else "atribuicao__assistido__nome"

    itens_qs = (
        ItemEntrega.objects
        .select_related(
            "lote",
            "lote__beneficio",
            "atribuicao",
            "atribuicao__assistido",
            "atribuicao__beneficio",
        )
        .filter(lote_id=lote.id)
        .order_by(order)
    )

    entregues = itens_qs.filter(entregue=True)
    pendentes = itens_qs.filter(entregue=False)
    return lote, itens_qs, entregues, pendentes


def historico_itens_por_assistido(
    *,
    q: str = "",
    data_ini: str = "",
    data_fim: str = "",
    beneficio_id: str = "",
    status: str = "todos",
) -> QuerySet[ItemEntrega]:
    """
    Histórico de itens (ItemEntrega) com filtros:
      - q: nome/cpf/telefone do assistido
      - data_ini/data_fim: intervalo baseado em lote.data_entrega
      - beneficio_id: lote.beneficio_id
      - status: todos/entregue/pendente
    """
    status = _normalize_status(status)

    qs = (
        ItemEntrega.objects
        .select_related(
            "lote",
            "lote__beneficio",
            "atribuicao",
            "atribuicao__assistido",
        )
    )

    di = _parse_date(data_ini)
    df = _parse_date(data_fim)
    if di:
        qs = qs.filter(lote__data_entrega__gte=di)
    if df:
        qs = qs.filter(lote__data_entrega__lte=df)

    beneficio_id = (beneficio_id or "").strip()
    if beneficio_id:
        try:
            qs = qs.filter(lote__beneficio_id=int(beneficio_id))
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

    # ordem padrão (a view pode sobrescrever)
    return qs.order_by("-lote__data_entrega", "atribuicao__assistido__nome", "-lote_id", "-id")

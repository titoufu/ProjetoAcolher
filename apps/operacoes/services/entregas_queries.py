# apps/operacoes/services/entregas_queries.py
from __future__ import annotations

from datetime import date
from typing import Optional, Tuple

from django.db.models import Count, Q
from django.shortcuts import get_object_or_404

from apps.beneficios.models import Beneficio, ItemEntrega, LoteEntrega


# =========================
# Helpers internos
# =========================

def _parse_date(s: str) -> Optional[date]:
    """Aceita 'YYYY-MM-DD'. Retorna None se vazio / inválido."""
    s = (s or "").strip()
    if not s:
        return None
    try:
        return date.fromisoformat(s)
    except ValueError:
        return None


def _normalize_status(status: str) -> str:
    """
    Normaliza status do filtro (tela histórico):
      - todos
      - entregue
      - pendente
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


# =========================
# Opções / selects
# =========================

def opcoes_beneficios():
    """Benefícios ordenados para preencher <select> de filtro."""
    return Beneficio.objects.order_by("nome", "id")


# =========================
# Consultas principais
# =========================

def lotes_com_resumo(
    *,
    q: str = "",
    data_ini: str = "",
    data_fim: str = "",
    beneficio_id: str = "",
    order_by: str = "-data_entrega",
):
    """
    QuerySet de LoteEntrega com anotações:
      - total
      - entregues
      - pendentes

    E filtros opcionais por:
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
            qs = qs.filter(beneficio_id=int(beneficio_id))
        except ValueError:
            pass

    q = (q or "").strip()
    if q:
        cond = Q(beneficio__nome__icontains=q)
        if q.isdigit():
            cond |= Q(id=int(q))
        qs = qs.filter(cond)

    qs = qs.annotate(
        total=Count("itens", distinct=True),
        entregues=Count("itens", filter=Q(itens__entregue=True), distinct=True),
        pendentes=Count("itens", filter=Q(itens__entregue=False), distinct=True),
    ).order_by(order_by, "-id")

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
      - texto: nome/cpf/telefone do assistido
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

    # Default do service (a view pode aplicar order_by por whitelist depois, se quiser)
    return qs.order_by("-lote__data_entrega", "atribuicao__assistido__nome", "-lote_id", "-id")


# =========================
# Detalhe de um lote
# =========================

def itens_do_lote(
    *,
    lote_id: str,
    order_by: str = "atribuicao__assistido__nome",
) -> Tuple[LoteEntrega, "ItemEntregaQuerySet", "ItemEntregaQuerySet", "ItemEntregaQuerySet"]:
    """
    Retorna:
      (lote, itens_qs, entregues_qs, pendentes_qs)
    """
    lote_id = (lote_id or "").strip()
    lote = get_object_or_404(
        LoteEntrega.objects.select_related("beneficio"),
        id=int(lote_id),
    )

    itens_qs = (
        ItemEntrega.objects
        .select_related("atribuicao__assistido", "atribuicao__beneficio", "lote", "lote__beneficio")
        .filter(lote_id=lote.id)
        .order_by(order_by)
    )

    entregues = itens_qs.filter(entregue=True)
    pendentes = itens_qs.filter(entregue=False)
    return lote, itens_qs, entregues, pendentes

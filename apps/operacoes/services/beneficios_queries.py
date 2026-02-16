# apps/operacoes/services/beneficios_queries.py
from __future__ import annotations

from django.db.models import Count, Q, QuerySet
from apps.beneficios.models import Beneficio, BeneficioAssistido


def _normalize_status(status: str) -> str:
    status = (status or "todos").strip().lower()
    mapa = {"todos": "todos", "ativos": "ativos", "encerrados": "encerrados"}
    return mapa.get(status, "todos")


def atribuicoes_qs(
    *,
    q: str = "",
    status: str = "todos",
    order_by: str = "assistido__nome",
) -> QuerySet[BeneficioAssistido]:
    status = _normalize_status(status)

    qs = (
        BeneficioAssistido.objects
        .select_related("assistido", "beneficio")
        .order_by(order_by, "beneficio__nome")
    )

    if status == "ativos":
        qs = qs.filter(ativo=True)
    elif status == "encerrados":
        qs = qs.filter(ativo=False)

    q = (q or "").strip()
    if q:
        qs = qs.filter(Q(assistido__nome__icontains=q) | Q(assistido__cpf__icontains=q))

    return qs


def beneficios_com_contadores() -> QuerySet[Beneficio]:
    return (
        Beneficio.objects
        .annotate(
            ativos_count=Count("assistidos_atribuidos", filter=Q(assistidos_atribuidos__ativo=True)),
            encerrados_count=Count("assistidos_atribuidos", filter=Q(assistidos_atribuidos__ativo=False)),
        )
        .order_by("nome", "id")
    )


def beneficio_assistidos_qs(
    *,
    beneficio_id: str = "",
    status: str = "ativos",
    order_by: str = "assistido__nome",
) -> QuerySet[BeneficioAssistido]:
    status = _normalize_status(status)

    qs = (
        BeneficioAssistido.objects
        .select_related("assistido", "beneficio")
        .order_by(order_by)
    )

    beneficio_id = (beneficio_id or "").strip()
    if beneficio_id:
        qs = qs.filter(beneficio_id=beneficio_id)

    if status == "ativos":
        qs = qs.filter(ativo=True)
    elif status == "encerrados":
        qs = qs.filter(ativo=False)

    return qs

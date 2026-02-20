from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q
from django.http import HttpResponseForbidden
from django.shortcuts import render
from .permissoes import pode_ver  # ajuste se estiver em outro lugar

from apps.beneficios.models import LoteEntrega, Beneficio


@login_required
def home_view(request):
    user = request.user
    grupos = list(user.groups.values_list("name", flat=True))

    contexto = {
        "user": user,
        "grupos": grupos,
        "is_admin": user.is_superuser,
    }
    return render(request, "operacoes/home.html", contexto)


@login_required
def consulta_lotes_resumo(request):
    beneficio_id = (request.GET.get("beneficio_id") or "").strip()
    data_ini = (request.GET.get("data_ini") or "").strip()
    data_fim = (request.GET.get("data_fim") or "").strip()

    qs = LoteEntrega.objects.select_related("beneficio")

    if beneficio_id.isdigit():
        qs = qs.filter(beneficio_id=int(beneficio_id))

    campo_data = "data_entrega" if hasattr(LoteEntrega, "data_entrega") else "data"

    if data_ini:
        qs = qs.filter(**{f"{campo_data}__gte": data_ini})
    if data_fim:
        qs = qs.filter(**{f"{campo_data}__lte": data_fim})

    qs = qs.annotate(
        total=Count("itens"),
        entregues=Count("itens", filter=Q(itens__entregue=True)),
        pendentes=Count("itens", filter=Q(itens__entregue=False)),
    ).order_by(f"-{campo_data}", "-id")

    beneficios = Beneficio.objects.order_by("nome")

    contexto = {
        "lotes": qs,
        "beneficios": beneficios,
        "beneficio_id": beneficio_id,
        "data_ini": data_ini,
        "data_fim": data_fim,
        "campo_data": campo_data,
    }
    return render(request, "operacoes/consultas/lotes_resumo.html", contexto)


@login_required
def consultas_home(request):
    if not pode_ver(request.user):
        return HttpResponseForbidden("Sem permissão.")
    return render(request, "operacoes/consultas_home.html")
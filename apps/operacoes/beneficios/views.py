# apps/operacoes/beneficios/views.py
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render

from apps.beneficios.models import Beneficio
from apps.operacoes.permissoes import pode_deletar, pode_editar, pode_ver
from .forms import BeneficioForm


@login_required
def beneficio_lista(request):
    if not pode_ver(request.user):
        return HttpResponseForbidden("Sem permissão.")

    beneficios = Beneficio.objects.all().order_by("id")

    # pega os campos uma vez
    fields = Beneficio._meta.fields

    linhas = []
    for b in beneficios:
        valores = []
        for field in fields:
            nome = field.name
            display_fn = getattr(b, f"get_{nome}_display", None)
            valor = display_fn() if callable(display_fn) else getattr(b, nome)
            valores.append(valor if valor not in (None, "") else "—")
        linhas.append((b, valores))

    contexto = {
        "fields": fields,
        "linhas": linhas,
        "pode_editar": pode_editar(request.user),
    }
    return render(request, "operacoes/beneficios/lista.html", contexto)



@login_required
def beneficio_detail(request, id):
    if not pode_ver(request.user):
        return HttpResponseForbidden("Sem permissão.")

    beneficio = get_object_or_404(Beneficio, id=id)

    # mesma ideia do Assistidos: exibir campos automaticamente (sem retrabalho)
    campos = []
    for field in beneficio._meta.fields:
        nome = field.name
        label = getattr(field, "verbose_name", nome).title()
        display_fn = getattr(beneficio, f"get_{nome}_display", None)
        valor = display_fn() if callable(display_fn) else getattr(beneficio, nome)
        campos.append((label, valor if valor not in (None, "") else "—"))

    contexto = {
        "beneficio": beneficio,
        "campos": campos,
        "pode_editar": pode_editar(request.user),
        "pode_deletar": pode_deletar(request.user),
    }
    return render(request, "operacoes/beneficios/detalhe.html", contexto)


@login_required
def beneficio_create(request):
    if not pode_editar(request.user):
        return HttpResponseForbidden("Sem permissão.")

    if request.method == "POST":
        form = BeneficioForm(request.POST)
        if form.is_valid():
            beneficio = form.save()
            return redirect("beneficios:beneficio_detail", id=beneficio.id)
    else:
        form = BeneficioForm()

    return render(
        request,
        "operacoes/beneficios/form.html",
        {"form": form, "modo": "novo", "pode_editar": True},
    )


@login_required
def beneficio_update(request, id):
    if not pode_editar(request.user):
        return HttpResponseForbidden("Sem permissão.")

    beneficio = get_object_or_404(Beneficio, id=id)

    if request.method == "POST":
        form = BeneficioForm(request.POST, instance=beneficio)
        if form.is_valid():
            form.save()
            return redirect("beneficios:beneficio_detail", id=beneficio.id)
    else:
        form = BeneficioForm(instance=beneficio)

    return render(
        request,
        "operacoes/beneficios/form.html",
        {"form": form, "modo": "editar", "beneficio": beneficio, "pode_editar": True},
    )


@login_required
def beneficio_delete(request, id):
    if not pode_deletar(request.user):
        return HttpResponseForbidden("Sem permissão.")

    beneficio = get_object_or_404(Beneficio, id=id)

    if request.method == "POST":
        beneficio.delete()
        return redirect("beneficios:beneficio_lista")

    return render(
        request,
        "operacoes/beneficios/confirm_delete.html",
        {"beneficio": beneficio, "pode_deletar": True},
    )

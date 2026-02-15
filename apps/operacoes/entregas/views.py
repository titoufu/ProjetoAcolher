from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db import IntegrityError
from django.contrib.auth.decorators import login_required, user_passes_test

from .forms import LoteEntregaForm
from apps.beneficios.models import LoteEntrega, ItemEntrega, BeneficioAssistido
from apps.operacoes.permissoes import pode_deletar,pode_ver
from django.http import HttpResponseForbidden


def lote_lista(request):
    lotes = LoteEntrega.objects.select_related("beneficio").order_by("-data_entrega")

    data_inicio = request.GET.get("data_inicio")
    data_fim = request.GET.get("data_fim")

    if data_inicio:
        lotes = lotes.filter(data_entrega__gte=data_inicio)

    if data_fim:
        lotes = lotes.filter(data_entrega__lte=data_fim)

    context = {
        "lotes": lotes,
        "data_inicio": data_inicio,
        "data_fim": data_fim,
    }
    return render(request, "operacoes/entregas/lote_lista.html", context)


def lote_create(request):
    if request.method == "POST":
        form = LoteEntregaForm(request.POST)
        if form.is_valid():
            try:
                lote = form.save()
            except IntegrityError:
                # ✅ mensagem única em português (validate_unique foi desativado no form)
                form.add_error(None, "Já existe um lote para este benefício nesta data.")
            else:
                # Gerar itens automaticamente
                if not lote.itens.exists():
                    atribuicoes = (
                        BeneficioAssistido.objects
                        .select_related("assistido", "beneficio")
                        .filter(beneficio=lote.beneficio, ativo=True)
                    )
                    atribuicoes = [a for a in atribuicoes if a.assistido.is_ativo]
                    itens = [ItemEntrega(lote=lote, atribuicao=a) for a in atribuicoes]
                    ItemEntrega.objects.bulk_create(itens, ignore_conflicts=True)

                messages.success(request, "Lote criado com sucesso.")
                return redirect("entregas:lote_lista")
    else:
        form = LoteEntregaForm()

    return render(request, "operacoes/entregas/lote_form.html", {"form": form})


def lote_detail(request, id):
    lote = get_object_or_404(
        LoteEntrega.objects.select_related("beneficio"),
        id=id
    )

    itens = (
        ItemEntrega.objects
        .select_related("atribuicao__assistido")
        .filter(lote=lote)
        .order_by("atribuicao__assistido__nome")
    )

    if request.method == "POST":
        marcados = request.POST.getlist("entregue")
        marcados_ids = {int(x) for x in marcados if x.isdigit()}

        for item in itens:
            novo_valor = item.id in marcados_ids
            if item.entregue != novo_valor:
                item.entregue = novo_valor
                item.save(update_fields=["entregue"])

        messages.success(request, "Checklist atualizado com sucesso.")
        return redirect("entregas:lote_detail", id=lote.id)

    total = itens.count()
    entregues = itens.filter(entregue=True).count()
    pendentes = total - entregues

    context = {
        "lote": lote,
        "itens": itens,
        "total": total,
        "entregues": entregues,
        "pendentes": pendentes,
    }
    return render(request, "operacoes/entregas/lote_detalhe.html", context)


def lote_update(request, id):
    lote = get_object_or_404(LoteEntrega, id=id)

    if request.method == "POST":
        form = LoteEntregaForm(request.POST, instance=lote)
        if form.is_valid():
            form.save()
            messages.success(request, "Lote atualizado com sucesso.")
            return redirect("entregas:lote_lista")
    else:
        form = LoteEntregaForm(instance=lote)

    return render(request, "operacoes/entregas/lote_form.html", {"form": form})


@login_required

def lote_delete(request, id):
    if not pode_deletar(request.user):
        return HttpResponseForbidden("Apenas o supervisor pode excluir lotes.")

    lote = get_object_or_404(LoteEntrega.objects.select_related("beneficio"), id=id)

    entregues_count = ItemEntrega.objects.filter(lote=lote, entregue=True).count()

    # 🔒 Regra: lote com entrega marcada NÃO pode ser excluído (por ninguém comum).
    # Supervisor tem acesso ao delete, mas deve ser advertido.
    if request.method == "POST":
        if entregues_count > 0:
            messages.error(request, "Este lote possui entregas marcadas e não pode ser excluído.")
            return redirect("entregas:lote_lista")

        lote.delete()
        messages.success(request, "Lote excluído com sucesso.")
        return redirect("entregas:lote_lista")

    return render(
        request,
        "operacoes/entregas/lote_confirm_delete.html",
        {"lote": lote, "entregues_count": entregues_count},
    )
@login_required
def lote_print(request, id):
    lote = get_object_or_404(
        LoteEntrega.objects.select_related("beneficio"),
        id=id
    )

    itens = (
        ItemEntrega.objects
        .select_related("atribuicao__assistido")
        .filter(lote=lote)
        .order_by("atribuicao__assistido__nome")
    )

    total = itens.count()
    entregues = itens.filter(entregue=True).count()
    pendentes = total - entregues

    context = {
        "lote": lote,
        "itens": itens,
        "total": total,
        "entregues": entregues,
        "pendentes": pendentes,
    }

    # ✅ AQUI é onde o rename impacta:
    return render(request, "operacoes/entregas/lote_detalhe_print.html", context)
    
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from django.shortcuts import render
from django.shortcuts import get_object_or_404, redirect, render
from apps.assistidos.models import Assistido
from apps.operacoes.permissoes import pode_editar, pode_ver
from apps.beneficios.models import BeneficioAssistido
from django.contrib import messages
from django.utils import timezone
from django.views.decorators.http import require_POST




@login_required
def selecionar_assistido_para_atribuicao(request):
    if not pode_ver(request.user):
        return HttpResponseForbidden("Sem permissão.")

    assistidos = Assistido.objects.filter(status="ATIVO").order_by("nome")

    contexto = {
        "assistidos": assistidos,
        "pode_editar": pode_editar(request.user),
    }
    return render(request, "operacoes/atribuicoes/selecionar_assistido.html", contexto)

@login_required
def atribuicoes_lista(request):
    if not pode_ver(request.user):
        return HttpResponseForbidden("Sem permissão.")

    atribuicoes = (
        BeneficioAssistido.objects
        .filter(ativo=True)
        .select_related("assistido", "beneficio")
        .order_by("assistido__nome", "beneficio__nome")
    )
    # agrupar por assistido
    grupos = {}
    for a in atribuicoes:
        grupos.setdefault(a.assistido, []).append(a)

    contexto = {
        "grupos": grupos,           # {assistido_obj: [atrib1, atrib2, ...]}
    }
    return render(request, "operacoes/atribuicoes/lista.html", contexto)


@login_required
def atribuicao_detail(request, pk):
    atribuicao = get_object_or_404(BeneficioAssistido, pk=pk)

    # você já tem um detalhe.html anexado — vamos usar ele
    return render(request, "operacoes/atribuicoes/detalhe.html", {"atribuicao": atribuicao})


@login_required
def atribuicao_update(request, pk):
    if not pode_editar(request.user):
        messages.error(request, "Sem permissão para editar atribuições.")
        return redirect("atribuicoes:atribuicoes_lista")

    atribuicao = get_object_or_404(BeneficioAssistido, pk=pk)

    # seu form já existe (BeneficioAssistidoForm) no app assistidos/forms.py (pelo traceback)
    from apps.operacoes.assistidos.forms import BeneficioAssistidoForm

    if request.method == "POST":
        form = BeneficioAssistidoForm(request.POST, instance=atribuicao)
        if form.is_valid():
            form.save()
            messages.success(request, "Atribuição atualizada com sucesso.")
            return redirect("atribuicoes:atribuicoes_lista")
    else:
        form = BeneficioAssistidoForm(instance=atribuicao)

    # você já tem um form.html anexado — vamos usar ele
    return render(
        request,
        "operacoes/atribuicoes/form.html",
        {"form": form, "modo": "editar", "atribuicao": atribuicao},
    )


@login_required
@require_POST
def atribuicao_encerrar(request, pk):
    if not pode_editar(request.user):
        messages.error(request, "Sem permissão para encerrar atribuições.")
        return redirect("atribuicoes:atribuicoes_lista")

    atribuicao = get_object_or_404(BeneficioAssistido, pk=pk)

    if not atribuicao.ativo:
        messages.info(request, "Esta atribuição já está encerrada.")
        return redirect("atribuicoes:atribuicoes_lista")

    # ✅ regra: encerrar sem modal => término = hoje
    atribuicao.data_termino = timezone.localdate()
    atribuicao.ativo = False
    atribuicao.save(update_fields=["data_termino", "ativo"])

    messages.success(request, "Atribuição encerrada com sucesso.")
    return redirect("atribuicoes:atribuicoes_lista")


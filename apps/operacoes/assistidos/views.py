from django.utils import timezone
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.db import IntegrityError
from django.contrib import messages
from apps.assistidos.models import Assistido
from apps.operacoes.permissoes import pode_deletar, pode_editar, pode_ver
from apps.beneficios.models import BeneficioAssistido

from .forms import AssistidoForm, BeneficioAssistidoForm


# =========================================================
# LISTA (filtro: nome + mês nascimento)
# =========================================================
@login_required
def lista_assistidos(request):
    if not pode_ver(request.user):
        return HttpResponseForbidden("Sem permissão.")

    qs = Assistido.objects.all()

    q_nome = (request.GET.get("nome") or "").strip()
    mes = (request.GET.get("mes") or "").strip()

    if q_nome:
        qs = qs.filter(nome__icontains=q_nome)

    if mes:
        qs = qs.filter(data_nascimento__month=int(mes))

    contexto = {
        "assistidos": qs,
        "pode_editar": pode_editar(request.user),
        "f_nome": q_nome,
        "f_mes": mes,
    }
    return render(request, "operacoes/assistidos/lista.html", contexto)


# =========================================================
# DETALHE (seções + regra status INATIVO)
# =========================================================
@login_required
def assistido_detail(request, id):
    if not pode_ver(request.user):
        return HttpResponseForbidden("Sem permissão.")

    assistido = get_object_or_404(Assistido, id=id)

    def valor_campo(nome):
        display_fn = getattr(assistido, f"get_{nome}_display", None)
        if callable(display_fn):
            v = display_fn()
        else:
            v = getattr(assistido, nome, None)

        if v is None or v == "":
            return "—"

        if hasattr(v, "strftime"):
            try:
                return v.strftime("%d/%m/%Y")
            except Exception:
                return str(v)

        return v

    # -------- Identificação (sempre) --------
    identificacao = [
        ("Nome", (assistido.nome or "—").title()),
        ("CPF", assistido.cpf_formatado or "—"),
        ("Data de Nascimento", valor_campo("data_nascimento")),
        ("Telefone", getattr(assistido, "telefone_formatado", "") or valor_campo("telefone")),
        ("Status", valor_campo("status")),
    ]

    # -------- Se INATIVO: mostrar data/motivo --------
    if assistido.status == "INATIVO":
        identificacao.append(("Data de Inativação", valor_campo("data_inativacao")))
        identificacao.append(("Motivo de Inativação", valor_campo("motivo_inativacao")))

    # -------- Seções --------
    secoes = {
        "Identificação": identificacao,
        "Endereço": [
            ("Logradouro", valor_campo("logradouro")),
            ("Número", valor_campo("numero")),
            ("Complemento", valor_campo("complemento")),
            ("Bairro", valor_campo("bairro")),
            ("Cidade", valor_campo("cidade")),
            ("UF", valor_campo("uf")),
            ("CEP", assistido.cep_formatado or "—"),
        ],
        "Situação Socioeconômica": [
            ("Situação de Trabalho", valor_campo("sit_trabalho")),
            ("Responsável pela Renda", valor_campo("responsavel_renda")),
            ("Faixa de Renda", valor_campo("faixa_renda")),
            ("Tipo de Moradia", valor_campo("tipo_moradia")),
            ("Material da Moradia", valor_campo("material_moradia")),
            ("Área de Risco", valor_campo("area_risco")),
            ("Sabe Ler/Escrever", valor_campo("sabe_ler_escrever")),
            ("Escolaridade", valor_campo("escolaridade")),
        ],
        "Condições de Saúde": [
            ("Diabetes", valor_campo("diabetes")),
            ("Pressão Alta", valor_campo("pressao_alta")),
            ("Medicação de Uso Contínuo", valor_campo("medic_uso_continuo")),
            ("Doença Permanente", valor_campo("doenca_permanente")),
        ],
        "Programa": [
            ("Ingresso no Programa", valor_campo("data_inicio_apoio")),
        ],
    }

    contexto = {
        "assistido": assistido,
        "secoes": secoes,
        "pode_editar": pode_editar(request.user),
        "pode_deletar": pode_deletar(request.user),
    }
    return render(request, "operacoes/assistidos/detalhe.html", contexto)


# =========================================================
# CREATE
# =========================================================
@login_required
def assistido_create(request):
    if not pode_editar(request.user):
        return HttpResponseForbidden("Sem permissão para criar.")

    if request.method == "POST":
        form = AssistidoForm(request.POST)
        if form.is_valid():
            assistido = form.save()
            return redirect("assistidos:assistido_detail", id=assistido.id)
    else:
        form = AssistidoForm()

    return render(
        request,
        "operacoes/assistidos/form.html",
        {"form": form, "modo": "criar"},
    )


# =========================================================
# UPDATE
# =========================================================
@login_required
def assistido_update(request, id):
    if not pode_editar(request.user):
        return HttpResponseForbidden("Sem permissão para editar.")

    assistido = get_object_or_404(Assistido, id=id)

    if request.method == "POST":
        form = AssistidoForm(request.POST, instance=assistido)
        if form.is_valid():
            form.save()
            return redirect("assistidos:assistido_detail", id=assistido.id)
    else:
        form = AssistidoForm(instance=assistido)

    return render(
        request,
        "operacoes/assistidos/form.html",
        {"form": form, "modo": "editar", "assistido": assistido},
    )


# =========================================================
# DELETE
# =========================================================
@login_required
def assistido_delete(request, id):
    if not pode_deletar(request.user):
        return HttpResponseForbidden("Sem permissão para deletar.")

    assistido = get_object_or_404(Assistido, id=id)

    if request.method == "POST":
        assistido.delete()
        return redirect("assistidos:assistidos_lista")

    return render(
        request,
        "operacoes/assistidos/confirm_delete.html",
        {"assistido": assistido},
    )


# =========================================================
# BENEFÍCIOS DO ASSISTIDO
# =========================================================
@login_required
def assistido_beneficios(request, id):
    if not pode_ver(request.user):
        return HttpResponseForbidden("Sem permissão.")

    assistido = get_object_or_404(Assistido, id=id)

    atribuicoes = (
        BeneficioAssistido.objects.filter(assistido=assistido)
        .select_related("beneficio")
        .order_by("-criado_em")
    )

    contexto = {
        "assistido": assistido,
        "atribuicoes": atribuicoes,
        "pode_editar": pode_editar(request.user),
        "pode_deletar": pode_deletar(request.user),
    }
    return render(request, "operacoes/assistidos/beneficios.html", contexto)

# =========================================================
# ATRIBUIR BENEFÍCIO AO ASSISTIDO
# =========================================================
@login_required
def assistido_beneficio_create(request, id):
    if not pode_editar(request.user):
        return HttpResponseForbidden("Sem permissão para atribuir benefício.")

    assistido = get_object_or_404(Assistido, id=id)

    if assistido.status != "ATIVO":
        return HttpResponseForbidden(
            "Não é permitido atribuir benefícios a assistidos INATIVOS."
        )

    if request.method == "POST":
        atribuicao = BeneficioAssistido(assistido=assistido)
        form = BeneficioAssistidoForm(request.POST, instance=atribuicao)
        if form.is_valid():
            try:
                form.save()
                messages.success(request, "Atribuição realizada com sucesso.")
                return redirect("atribuicoes:atribuicoes_lista")
            except IntegrityError:
                mensagem = "Este benefício já está atribuído a este assistido."
                form.add_error("beneficio", mensagem)
                messages.error(request, mensagem)
    else:
        atribuicao = BeneficioAssistido(assistido=assistido, data_inicio=timezone.localdate())
        form = BeneficioAssistidoForm(instance=atribuicao)

    contexto = {
        "assistido": assistido,
        "form": form,
        "pode_editar": pode_editar(request.user),
        "pode_deletar": pode_deletar(request.user),
        "pode_ver": pode_ver(request.user),
        "modo": "novo",
    }
    return render(
        request,
        "operacoes/assistidos/beneficio_atribuir.html",
        contexto
    )

@login_required
def assistido_beneficio_update(request, id, bid):
    if not pode_editar(request.user):
        return HttpResponseForbidden("Sem permissão para editar benefício.")

    assistido = get_object_or_404(Assistido, id=id)

    if assistido.status != "ATIVO":
        return HttpResponseForbidden("Não é permitido alterar benefícios de assistidos INATIVOS.")

    atribuicao = get_object_or_404(BeneficioAssistido, id=bid, assistido=assistido)

    if request.method == "POST":
        form = BeneficioAssistidoForm(request.POST, instance=atribuicao)
        if form.is_valid():
            try:
                form.save()
                messages.success(request, "Atribuição atualizada com sucesso.")
                return redirect("atribuicoes:atribuicoes_lista")
            except IntegrityError:
                form.add_error("beneficio", "Este benefício já está atribuído a este assistido.")
    else:
        # ✅ aqui é o ponto crítico: editar SEMPRE vem com instance
        form = BeneficioAssistidoForm(instance=atribuicao)

    contexto = {
        "assistido": assistido,
        "form": form,
        "modo": "editar",
        "atribuicao": atribuicao,
        "pode_editar": pode_editar(request.user),
        "pode_deletar": pode_deletar(request.user),
        "pode_ver": pode_ver(request.user),
    }
    return render(request, "operacoes/assistidos/beneficio_atribuir.html", contexto)



@login_required
def assistido_beneficio_encerrar(request, id, bid):
    if not pode_editar(request.user):
        return HttpResponseForbidden("Sem permissão para encerrar benefício.")

    assistido = get_object_or_404(Assistido, id=id)

    if assistido.status != "ATIVO":
        return HttpResponseForbidden("Não é permitido encerrar benefícios de assistidos INATIVOS.")

    atribuicao = get_object_or_404(BeneficioAssistido, id=bid, assistido=assistido)

    if request.method == "POST":
        atribuicao.data_termino = timezone.localdate()
        atribuicao.save()  # sem update_fields
        messages.success(request, "Atribuição encerrada com sucesso.")
    return redirect("atribuicoes:atribuicoes_lista")

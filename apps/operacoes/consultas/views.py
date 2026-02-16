from __future__ import annotations

from datetime import date

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q
from django.http import HttpResponse, HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.dateparse import parse_date

from apps.assistidos.models import Assistido, TriSimNao
from apps.beneficios.models import Beneficio, BeneficioAssistido, ItemEntrega, LoteEntrega
from apps.operacoes.permissoes import pode_ver

from apps.operacoes.services.assistidos_queries import (
    assistidos_identificacao_qs,
    assistidos_saude_qs,
    assistidos_socioeconomico_qs,
)
from apps.operacoes.services.entregas_queries import (
    historico_itens_por_assistido,
    itens_do_lote,
    lotes_com_resumo,
    opcoes_beneficios,
)

# =========================
#  ORDENAÇÃO (WHITELISTS)
# =========================

ORDERS_ENTREGAS_LOTES = {
    "data_entrega": "data_entrega",
    "-data_entrega": "-data_entrega",
    "beneficio__nome": "beneficio__nome",
    "-beneficio__nome": "-beneficio__nome",
    "total": "total",
    "-total": "-total",
    "entregues": "entregues",
    "-entregues": "-entregues",
    "pendentes": "pendentes",
    "-pendentes": "-pendentes",
}

ORDERS_ENTREGAS_LOTE = {
    "atribuicao__assistido__nome": "atribuicao__assistido__nome",
    "-atribuicao__assistido__nome": "-atribuicao__assistido__nome",
    "entregue": "entregue",
    "-entregue": "-entregue",
}

ORDERS_ENTREGAS_ASSISTIDO = {
    "atribuicao__assistido__nome": "atribuicao__assistido__nome",
    "-atribuicao__assistido__nome": "-atribuicao__assistido__nome",
    "lote__data_entrega": "lote__data_entrega",
    "-lote__data_entrega": "-lote__data_entrega",
    "lote__beneficio__nome": "lote__beneficio__nome",
    "-lote__beneficio__nome": "-lote__beneficio__nome",
    "entregue": "entregue",
    "-entregue": "-entregue",
}

ORDERS_IDENTIFICACAO = {
    "nome": "nome",
    "-nome": "-nome",
    "status": "status",
    "-status": "-status",
    "cep": "cep",
    "-cep": "-cep",
    "logradouro": "logradouro",
    "-logradouro": "-logradouro",
}

ORDERS_SAUDE = {
    "nome": "nome",
    "-nome": "-nome",
    "diabetes": "diabetes",
    "-diabetes": "-diabetes",
    "pressao_alta": "pressao_alta",
    "-pressao_alta": "-pressao_alta",
    "medic_uso_continuo": "medic_uso_continuo",
    "-medic_uso_continuo": "-medic_uso_continuo",
    "doenca_permanente": "doenca_permanente",
    "-doenca_permanente": "-doenca_permanente",
}

ORDERS_SOCIOECONOMICO = {
    "nome": "nome",
    "-nome": "-nome",
    "sit_trabalho": "sit_trabalho",
    "-sit_trabalho": "-sit_trabalho",
    "faixa_renda": "faixa_renda",
    "-faixa_renda": "-faixa_renda",
    "tipo_moradia": "tipo_moradia",
    "-tipo_moradia": "-tipo_moradia",
    "escolaridade": "escolaridade",
    "-escolaridade": "-escolaridade",
}

ORDERS_BENEFICIO_ASSISTIDOS = {
    "assistido__nome": "assistido__nome",
    "-assistido__nome": "-assistido__nome",
    "data_inicio": "data_inicio",
    "-data_inicio": "-data_inicio",
    "data_termino": "data_termino",
    "-data_termino": "-data_termino",
}

# =========================
#  HELPERS DE ORDER
# =========================

def _get_order(request, mapping, default):
    raw = (request.GET.get("o") or default).strip()
    return mapping.get(raw, default)

def _get_order_socioeconomico(request):
    return _get_order(request, ORDERS_SOCIOECONOMICO, "nome")

def _get_order_saude(request):
    return _get_order(request, ORDERS_SAUDE, "nome")

def _get_order_identificacao(request):
    return _get_order(request, ORDERS_IDENTIFICACAO, "nome")

def _get_order_entregas_assistido(request):
    return _get_order(request, ORDERS_ENTREGAS_ASSISTIDO, "-lote__data_entrega")

def _get_order_entregas_lotes(request):
    return _get_order(request, ORDERS_ENTREGAS_LOTES, "-data_entrega")

def _get_order_entregas_lote(request):
    return _get_order(request, ORDERS_ENTREGAS_LOTE, "atribuicao__assistido__nome")

def _get_order_beneficio_assistidos(request):
    return _get_order(request, ORDERS_BENEFICIO_ASSISTIDOS, "assistido__nome")

# =========================
#  CONSULTAS - ASSISTIDOS
# =========================

@login_required
def identificacao_lista(request):
    if not pode_ver(request.user):
        return HttpResponse("Sem permissão.", status=403)

    qs = assistidos_identificacao_qs(
        q=(request.GET.get("q") or "").strip(),
        status=(request.GET.get("status") or "").strip(),
        logradouro=(request.GET.get("logradouro") or "").strip(),
        cep=(request.GET.get("cep") or "").strip(),
        order_by=_get_order_identificacao(request),
    )
    return render(request, "operacoes/consultas/identificacao_lista.html", {"assistidos": qs, "total": qs.count()})


@login_required
def identificacao_print(request):
    if not pode_ver(request.user):
        return HttpResponse("Sem permissão.", status=403)

    qs = assistidos_identificacao_qs(
        q=(request.GET.get("q") or "").strip(),
        status=(request.GET.get("status") or "").strip(),
        logradouro=(request.GET.get("logradouro") or "").strip(),
        cep=(request.GET.get("cep") or "").strip(),
        order_by=_get_order_identificacao(request),
    )
    return render(request, "operacoes/consultas/identificacao_print.html", {"assistidos": qs, "total": qs.count()})


@login_required
def saude_lista(request):
    if not pode_ver(request.user):
        return HttpResponse("Sem permissão.", status=403)

    qs = assistidos_saude_qs(
        q=(request.GET.get("q") or "").strip(),
        status=(request.GET.get("status") or "").strip(),
        diabetes=(request.GET.get("diabetes") or "").strip(),
        pressao_alta=(request.GET.get("pressao_alta") or "").strip(),
        medic_uso_continuo=(request.GET.get("medic_uso_continuo") or "").strip(),
        doenca_permanente=(request.GET.get("doenca_permanente") or "").strip(),
        order_by=_get_order_saude(request),
    )

    contexto = {
        "assistidos": qs,
        "total": qs.count(),
        "choices_diabetes": TriSimNao.choices,
        "choices_pressao_alta": TriSimNao.choices,
        "choices_medic_uso_continuo": TriSimNao.choices,
        "choices_doenca_permanente": TriSimNao.choices,
    }
    return render(request, "operacoes/consultas/saude_lista.html", contexto)


@login_required
def saude_print(request):
    if not pode_ver(request.user):
        return HttpResponse("Sem permissão.", status=403)

    qs = assistidos_saude_qs(
        q=(request.GET.get("q") or "").strip(),
        status=(request.GET.get("status") or "").strip(),
        diabetes=(request.GET.get("diabetes") or "").strip(),
        pressao_alta=(request.GET.get("pressao_alta") or "").strip(),
        medic_uso_continuo=(request.GET.get("medic_uso_continuo") or "").strip(),
        doenca_permanente=(request.GET.get("doenca_permanente") or "").strip(),
        order_by=_get_order_saude(request),
    )

    contexto = {
        "assistidos": qs,
        "total": qs.count(),
        "choices_diabetes": TriSimNao.choices,
        "choices_pressao_alta": TriSimNao.choices,
        "choices_medic_uso_continuo": TriSimNao.choices,
        "choices_doenca_permanente": TriSimNao.choices,
    }
    return render(request, "operacoes/consultas/saude_print.html", contexto)


@login_required
def socioeconomico_lista(request):
    if not pode_ver(request.user):
        return HttpResponse("Sem permissão.", status=403)

    qs = assistidos_socioeconomico_qs(
        q=(request.GET.get("q") or "").strip(),
        status=(request.GET.get("status") or "").strip(),
        sit_trabalho=(request.GET.get("sit_trabalho") or "").strip(),
        faixa_renda=(request.GET.get("faixa_renda") or "").strip(),
        tipo_moradia=(request.GET.get("tipo_moradia") or "").strip(),
        escolaridade=(request.GET.get("escolaridade") or "").strip(),
        area_risco=(request.GET.get("area_risco") or "").strip(),
        order_by=_get_order_socioeconomico(request),
    )

    contexto = {
        "assistidos": qs,
        "total": qs.count(),
        "choices_sit_trabalho": Assistido._meta.get_field("sit_trabalho").choices,
        "choices_faixa_renda": Assistido._meta.get_field("faixa_renda").choices,
        "choices_tipo_moradia": Assistido._meta.get_field("tipo_moradia").choices,
        "choices_escolaridade": Assistido._meta.get_field("escolaridade").choices,
        "choices_area_risco": Assistido._meta.get_field("area_risco").choices,
    }
    return render(request, "operacoes/consultas/socioeconomico_lista.html", contexto)


@login_required
def socioeconomico_print(request):
    if not pode_ver(request.user):
        return HttpResponse("Sem permissão.", status=403)

    qs = assistidos_socioeconomico_qs(
        q=(request.GET.get("q") or "").strip(),
        status=(request.GET.get("status") or "").strip(),
        sit_trabalho=(request.GET.get("sit_trabalho") or "").strip(),
        faixa_renda=(request.GET.get("faixa_renda") or "").strip(),
        tipo_moradia=(request.GET.get("tipo_moradia") or "").strip(),
        escolaridade=(request.GET.get("escolaridade") or "").strip(),
        area_risco=(request.GET.get("area_risco") or "").strip(),
        order_by=_get_order_socioeconomico(request),
    )

    contexto = {
        "assistidos": qs,
        "total": qs.count(),
        "choices_sit_trabalho": Assistido._meta.get_field("sit_trabalho").choices,
        "choices_faixa_renda": Assistido._meta.get_field("faixa_renda").choices,
        "choices_tipo_moradia": Assistido._meta.get_field("tipo_moradia").choices,
        "choices_escolaridade": Assistido._meta.get_field("escolaridade").choices,
        "choices_area_risco": Assistido._meta.get_field("area_risco").choices,
    }
    return render(request, "operacoes/consultas/socioeconomico_print.html", contexto)

# =========================
#  CONSULTAS - ATRIBUIÇÕES
# =========================
# (mantive seu código como está; podemos migrar para service depois)

@login_required
def atribuicoes_consulta(request):
    if not pode_ver(request.user):
        return HttpResponseForbidden("Sem permissão.")

    status = (request.GET.get("status") or "todos").strip().lower()
    q = (request.GET.get("q") or "").strip()

    qs = (
        BeneficioAssistido.objects
        .select_related("assistido", "beneficio")
        .order_by("assistido__nome", "beneficio__nome")
    )

    if status == "ativos":
        qs = qs.filter(ativo=True)
    elif status == "encerrados":
        qs = qs.filter(ativo=False)
    else:
        status = "todos"

    if q:
        qs = qs.filter(Q(assistido__nome__icontains=q) | Q(assistido__cpf__icontains=q))

    grupos = {}
    for a in qs:
        grupos.setdefault(a.assistido, []).append(a)

    contexto = {"grupos": grupos, "status": status, "q": q, "total": qs.count()}
    return render(request, "operacoes/consultas/atribuicoes_consulta_lista.html", contexto)


@login_required
def atribuicoes_consulta_print(request):
    if not pode_ver(request.user):
        return HttpResponseForbidden("Sem permissão.")

    status = (request.GET.get("status") or "todos").strip().lower()
    q = (request.GET.get("q") or "").strip()

    qs = (
        BeneficioAssistido.objects
        .select_related("assistido", "beneficio")
        .order_by("assistido__nome", "beneficio__nome")
    )

    if status == "ativos":
        qs = qs.filter(ativo=True)
    elif status == "encerrados":
        qs = qs.filter(ativo=False)
    else:
        status = "todos"

    if q:
        qs = qs.filter(Q(assistido__nome__icontains=q) | Q(assistido__cpf__icontains=q))

    grupos = {}
    for a in qs:
        grupos.setdefault(a.assistido, []).append(a)

    contexto = {"grupos": grupos, "status": status, "q": q, "total": qs.count()}
    return render(request, "operacoes/consultas/atribuicoes_consulta_print.html", contexto)

# =========================
#  CONSULTAS - BENEFÍCIO x ASSISTIDOS
# =========================

@login_required
def beneficio_assistidos_consulta(request):
    if not pode_ver(request.user):
        return HttpResponseForbidden("Sem permissão.")

    beneficio_id = (request.GET.get("beneficio_id") or "").strip()
    status = (request.GET.get("status") or "ativos").strip().lower()
    order = _get_order_beneficio_assistidos(request)

    beneficios = (
        Beneficio.objects
        .annotate(
            ativos_count=Count("assistidos_atribuidos", filter=Q(assistidos_atribuidos__ativo=True)),
            encerrados_count=Count("assistidos_atribuidos", filter=Q(assistidos_atribuidos__ativo=False)),
        )
        .order_by("nome", "id")
    )

    qs = BeneficioAssistido.objects.select_related("assistido", "beneficio").order_by(order)

    if beneficio_id:
        qs = qs.filter(beneficio_id=beneficio_id)

    if status == "ativos":
        qs = qs.filter(ativo=True)
    elif status == "encerrados":
        qs = qs.filter(ativo=False)
    else:
        status = "todos"

    contexto = {
        "beneficios": beneficios,
        "beneficio_id": beneficio_id,
        "status": status,
        "atribuicoes": qs,
        "total": qs.count(),
    }
    return render(request, "operacoes/consultas/beneficio_assistidos_lista.html", contexto)


@login_required
def beneficio_assistidos_print(request):
    if not pode_ver(request.user):
        return HttpResponseForbidden("Sem permissão.")

    beneficio_id = (request.GET.get("beneficio_id") or "").strip()
    status = (request.GET.get("status") or "ativos").strip().lower()
    order = _get_order_beneficio_assistidos(request)

    beneficios = (
        Beneficio.objects
        .annotate(
            ativos_count=Count("assistidos_atribuidos", filter=Q(assistidos_atribuidos__ativo=True)),
            encerrados_count=Count("assistidos_atribuidos", filter=Q(assistidos_atribuidos__ativo=False)),
        )
        .order_by("nome", "id")
    )

    qs = BeneficioAssistido.objects.select_related("assistido", "beneficio").order_by(order)

    if beneficio_id:
        qs = qs.filter(beneficio_id=beneficio_id)

    if status == "ativos":
        qs = qs.filter(ativo=True)
    elif status == "encerrados":
        qs = qs.filter(ativo=False)
    else:
        status = "todos"

    beneficio_sel = Beneficio.objects.filter(id=beneficio_id).first() if beneficio_id else None

    contexto = {
        "beneficios": beneficios,
        "beneficio_id": beneficio_id,
        "beneficio_sel": beneficio_sel,
        "status": status,
        "atribuicoes": qs,
        "total": qs.count(),
    }
    return render(request, "operacoes/consultas/beneficio_assistidos_print.html", contexto)

# =========================
#  CONSULTAS - ENTREGAS
# =========================

@login_required
def entregas_lotes_lista(request):
    if not pode_ver(request.user):
        return HttpResponseForbidden("Sem permissão.")

    q = (request.GET.get("q") or "").strip()
    data_ini = (request.GET.get("data_ini") or "").strip()
    data_fim = (request.GET.get("data_fim") or "").strip()
    beneficio_id = (request.GET.get("beneficio_id") or "").strip()

    qs = lotes_com_resumo(
        q=q,
        data_ini=data_ini,
        data_fim=data_fim,
        beneficio_id=beneficio_id,
        order_by=_get_order_entregas_lotes(request),
    )

    contexto = {
        "lotes": qs,
        "total": qs.count(),
        "beneficios": opcoes_beneficios(),
        "q": q,
        "beneficio_id": beneficio_id,
        "data_ini": data_ini,
        "data_fim": data_fim,
    }
    return render(request, "operacoes/consultas/entregas_lotes_lista.html", contexto)


@login_required
def entregas_lotes_print(request):
    if not pode_ver(request.user):
        return HttpResponseForbidden("Sem permissão.")

    q = (request.GET.get("q") or "").strip()
    data_ini = (request.GET.get("data_ini") or "").strip()
    data_fim = (request.GET.get("data_fim") or "").strip()
    beneficio_id = (request.GET.get("beneficio_id") or "").strip()

    qs = lotes_com_resumo(
        q=q,
        data_ini=data_ini,
        data_fim=data_fim,
        beneficio_id=beneficio_id,
        order_by=_get_order_entregas_lotes(request),
    )

    contexto = {
        "lotes": qs,
        "total": qs.count(),
        "beneficios": opcoes_beneficios(),
        "q": q,
        "beneficio_id": beneficio_id,
        "data_ini": data_ini,
        "data_fim": data_fim,
    }
    return render(request, "operacoes/consultas/entregas_lotes_print.html", contexto)


@login_required
def entregas_lote_detalhe(request):
    if not pode_ver(request.user):
        return HttpResponseForbidden("Sem permissão.")

    lote_id = (request.GET.get("lote_id") or "").strip()
    order = _get_order_entregas_lote(request)
    lote, itens_qs, entregues, pendentes = itens_do_lote(lote_id=lote_id, order_by=order)

    contexto = {
        "lote": lote,
        "itens": itens_qs,
        "entregues": entregues,
        "pendentes": pendentes,
        "total": itens_qs.count(),
        "entregues_count": entregues.count(),
        "pendentes_count": pendentes.count(),
    }
    return render(request, "operacoes/consultas/entregas_lote_detalhe.html", contexto)


@login_required
def entregas_lote_print(request):
    if not pode_ver(request.user):
        return HttpResponseForbidden("Sem permissão.")

    lote_id = (request.GET.get("lote_id") or "").strip()
    order = _get_order_entregas_lote(request)
    lote, itens_qs, entregues, pendentes = itens_do_lote(lote_id=lote_id, order_by=order)

    contexto = {
        "lote": lote,
        "itens": itens_qs,
        "entregues": entregues,
        "pendentes": pendentes,
        "total": itens_qs.count(),
        "entregues_count": entregues.count(),
        "pendentes_count": pendentes.count(),
    }
    return render(request, "operacoes/consultas/entregas_lote_detalhe_print.html", contexto)


@login_required
def entregas_assistido_historico(request):
    if not pode_ver(request.user):
        return HttpResponseForbidden("Sem permissão.")

    q = (request.GET.get("q") or "").strip()
    data_ini = (request.GET.get("data_ini") or "").strip()
    data_fim = (request.GET.get("data_fim") or "").strip()
    beneficio_id = (request.GET.get("beneficio_id") or "").strip()
    status = (request.GET.get("status") or "todos").strip().lower()

    qs = historico_itens_por_assistido(
        q=q,
        data_ini=data_ini,
        data_fim=data_fim,
        beneficio_id=beneficio_id,
        status=status,
    ).order_by(_get_order_entregas_assistido(request))

    status_norm = status if status in {"todos", "entregue", "entregues", "pendente", "pendentes"} else "todos"

    contexto = {
        "q": q,
        "data_ini": data_ini,
        "data_fim": data_fim,
        "beneficio_id": beneficio_id,
        "status": status_norm,
        "beneficios": opcoes_beneficios(),
        "itens": qs,
        "total": qs.count(),
        "entregues_count": qs.filter(entregue=True).count(),
        "pendentes_count": qs.filter(entregue=False).count(),
    }
    return render(request, "operacoes/consultas/entregas_assistido_historico.html", contexto)


@login_required
def entregas_assistido_historico_print(request):
    if not pode_ver(request.user):
        return HttpResponseForbidden("Sem permissão.")

    q = (request.GET.get("q") or "").strip()
    data_ini = (request.GET.get("data_ini") or "").strip()
    data_fim = (request.GET.get("data_fim") or "").strip()
    beneficio_id = (request.GET.get("beneficio_id") or "").strip()
    status = (request.GET.get("status") or "todos").strip().lower()

    qs = historico_itens_por_assistido(
        q=q,
        data_ini=data_ini,
        data_fim=data_fim,
        beneficio_id=beneficio_id,
        status=status,
    ).order_by(_get_order_entregas_assistido(request))

    status_norm = status if status in {"todos", "entregue", "entregues", "pendente", "pendentes"} else "todos"

    contexto = {
        "q": q,
        "data_ini": data_ini,
        "data_fim": data_fim,
        "beneficio_id": beneficio_id,
        "status": status_norm,
        "beneficios": opcoes_beneficios(),
        "itens": qs,
        "total": qs.count(),
        "entregues_count": qs.filter(entregue=True).count(),
        "pendentes_count": qs.filter(entregue=False).count(),
    }
    return render(request, "operacoes/consultas/entregas_assistido_historico_print.html", contexto)


@login_required
def entregas_lote_chamada(request):
    if not pode_ver(request.user):
        return HttpResponseForbidden("Sem permissão.")

    data_ini = (request.GET.get("data_ini") or "").strip()
    data_fim = (request.GET.get("data_fim") or "").strip()
    beneficio_id = (request.GET.get("beneficio_id") or "").strip()

    lotes = LoteEntrega.objects.select_related("beneficio").order_by("-data_entrega", "-id")
    if data_ini:
        lotes = lotes.filter(data_entrega__gte=data_ini)
    if data_fim:
        lotes = lotes.filter(data_entrega__lte=data_fim)
    if beneficio_id:
        lotes = lotes.filter(beneficio_id=beneficio_id)

    lotes_list = []
    for l in lotes:
        total = ItemEntrega.objects.filter(lote=l).count()
        entregues = ItemEntrega.objects.filter(lote=l, entregue=True).count()
        l.total = total
        l.entregues = entregues
        l.pendentes = total - entregues
        lotes_list.append(l)

    contexto = {
        "lotes": lotes_list,
        "beneficios": Beneficio.objects.order_by("nome", "id"),
        "data_ini": data_ini,
        "data_fim": data_fim,
        "beneficio_id": beneficio_id,
        "total": len(lotes_list),
    }
    return render(request, "operacoes/consultas/entregas_lote_chamada.html", contexto)


@login_required
def entregas_lote_chamada_print(request):
    if not pode_ver(request.user):
        return HttpResponseForbidden("Sem permissão.")

    lote_id = (request.GET.get("lote_id") or "").strip()
    if not lote_id.isdigit():
        messages.error(request, "Informe um lote válido para imprimir a lista de chamada.")
        return redirect("consultas:entregas_lote_chamada")

    lote = get_object_or_404(LoteEntrega.objects.select_related("beneficio"), id=int(lote_id))
    itens_qs = ItemEntrega.objects.select_related("atribuicao__assistido").filter(lote=lote).order_by("atribuicao__assistido__nome")

    contexto = {"lote": lote, "itens": itens_qs, "total": itens_qs.count()}
    return render(request, "operacoes/consultas/entregas_lote_chamada_print.html", contexto)


@login_required
def consulta_lotes_resumo(request):
    if not pode_ver(request.user):
        return HttpResponseForbidden("Sem permissão.")

    q = (request.GET.get("q") or "").strip()
    beneficio_id = (request.GET.get("beneficio_id") or request.GET.get("beneficio") or "").strip()
    data_ini = (request.GET.get("data_ini") or request.GET.get("data_inicio") or request.GET.get("data_inicial") or "").strip()
    data_fim = (request.GET.get("data_fim") or request.GET.get("data_final") or "").strip()

    qs = lotes_com_resumo(
        q=q,
        data_ini=data_ini,
        data_fim=data_fim,
        beneficio_id=beneficio_id,
        order_by="-data_entrega",
    )

    contexto = {
        "lotes": qs,
        "beneficios": opcoes_beneficios(),
        "q": q,
        "beneficio_id": beneficio_id,
        "data_ini": data_ini,
        "data_fim": data_fim,
        "campo_data": "data_entrega",
    }
    return render(request, "operacoes/consultas/lotes_resumo.html", contexto)

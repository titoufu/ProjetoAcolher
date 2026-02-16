# apps/operacoes/consultas/views.py
from __future__ import annotations

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.dateparse import parse_date

from apps.beneficios.models import Beneficio, BeneficioAssistido, ItemEntrega, LoteEntrega
from apps.operacoes.permissoes import pode_ver

from apps.operacoes.services.assistidos_queries import (
    assistidos_choices_para_filtros,
    assistidos_identificacao_qs,
    assistidos_saude_qs,
    assistidos_socioeconomico_qs,
)
from apps.operacoes.services.beneficios_queries import (
    atribuicoes_qs,
    beneficio_assistidos_qs,
    beneficios_com_contadores,
)
from apps.operacoes.services.entregas_queries import (
    historico_itens_por_assistido,
    itens_do_lote,
    lotes_com_resumo,
    opcoes_beneficios,
)

# =========================
# Helpers de ordenação
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


def _get_order_entregas_assistido(request):
    raw = (request.GET.get("o") or "-lote__data_entrega").strip()
    return ORDERS_ENTREGAS_ASSISTIDO.get(raw, "-lote__data_entrega")


def _get_order_entregas_lotes(request):
    raw = (request.GET.get("o") or "-data_entrega").strip()
    return ORDERS_ENTREGAS_LOTES.get(raw, "-data_entrega")


def _get_order_entregas_lote(request):
    raw = (request.GET.get("o") or "atribuicao__assistido__nome").strip()
    return ORDERS_ENTREGAS_LOTE.get(raw, "atribuicao__assistido__nome")


# =========================
# ASSISTIDOS — Identificação
# =========================

@login_required
def identificacao_lista(request):
    if not pode_ver(request.user):
        return HttpResponseForbidden("Sem permissão.")

    qs = assistidos_identificacao_qs(
        q=request.GET.get("q", ""),
        status=request.GET.get("status", ""),
        logradouro=request.GET.get("logradouro", ""),
        cep=request.GET.get("cep", ""),
        order=request.GET.get("o", "nome"),
    )

    contexto = {
        "assistidos": qs,
        "total": qs.count(),
        "q": (request.GET.get("q") or "").strip(),
        "status": (request.GET.get("status") or "").strip(),
        "logradouro": (request.GET.get("logradouro") or "").strip(),
        "cep": (request.GET.get("cep") or "").strip(),
        "o": (request.GET.get("o") or "nome").strip(),
    }
    return render(request, "operacoes/consultas/identificacao_lista.html", contexto)


@login_required
def identificacao_print(request):
    if not pode_ver(request.user):
        return HttpResponseForbidden("Sem permissão.")

    qs = assistidos_identificacao_qs(
        q=request.GET.get("q", ""),
        status=request.GET.get("status", ""),
        logradouro=request.GET.get("logradouro", ""),
        cep=request.GET.get("cep", ""),
        order=request.GET.get("o", "nome"),
    )

    contexto = {
        "assistidos": qs,
        "total": qs.count(),
        "q": (request.GET.get("q") or "").strip(),
        "status": (request.GET.get("status") or "").strip(),
        "logradouro": (request.GET.get("logradouro") or "").strip(),
        "cep": (request.GET.get("cep") or "").strip(),
        "o": (request.GET.get("o") or "nome").strip(),
    }
    return render(request, "operacoes/consultas/identificacao_print.html", contexto)


# =========================
# ASSISTIDOS — Socioeconômico
# =========================

@login_required
def socioeconomico_lista(request):
    if not pode_ver(request.user):
        return HttpResponseForbidden("Sem permissão.")

    qs = assistidos_socioeconomico_qs(
        q=request.GET.get("q", ""),
        status=request.GET.get("status", ""),
        sit_trabalho=request.GET.get("sit_trabalho", ""),
        faixa_renda=request.GET.get("faixa_renda", ""),
        tipo_moradia=request.GET.get("tipo_moradia", ""),
        area_risco=request.GET.get("area_risco", ""),
        escolaridade=request.GET.get("escolaridade", ""),
        order=request.GET.get("o", "nome"),
    )

    contexto = {
        "assistidos": qs,
        "total": qs.count(),
        "q": (request.GET.get("q") or "").strip(),
        "status": (request.GET.get("status") or "").strip(),
        "sit_trabalho": (request.GET.get("sit_trabalho") or "").strip(),
        "faixa_renda": (request.GET.get("faixa_renda") or "").strip(),
        "tipo_moradia": (request.GET.get("tipo_moradia") or "").strip(),
        "area_risco": (request.GET.get("area_risco") or "").strip(),
        "escolaridade": (request.GET.get("escolaridade") or "").strip(),
        "o": (request.GET.get("o") or "nome").strip(),
        **assistidos_choices_para_filtros(),
    }
    return render(request, "operacoes/consultas/socioeconomico_lista.html", contexto)


@login_required
def socioeconomico_print(request):
    if not pode_ver(request.user):
        return HttpResponseForbidden("Sem permissão.")

    qs = assistidos_socioeconomico_qs(
        q=request.GET.get("q", ""),
        status=request.GET.get("status", ""),
        sit_trabalho=request.GET.get("sit_trabalho", ""),
        faixa_renda=request.GET.get("faixa_renda", ""),
        tipo_moradia=request.GET.get("tipo_moradia", ""),
        area_risco=request.GET.get("area_risco", ""),
        escolaridade=request.GET.get("escolaridade", ""),
        order=request.GET.get("o", "nome"),
    )

    contexto = {
        "assistidos": qs,
        "total": qs.count(),
        "q": (request.GET.get("q") or "").strip(),
        "status": (request.GET.get("status") or "").strip(),
        "sit_trabalho": (request.GET.get("sit_trabalho") or "").strip(),
        "faixa_renda": (request.GET.get("faixa_renda") or "").strip(),
        "tipo_moradia": (request.GET.get("tipo_moradia") or "").strip(),
        "area_risco": (request.GET.get("area_risco") or "").strip(),
        "escolaridade": (request.GET.get("escolaridade") or "").strip(),
        "o": (request.GET.get("o") or "nome").strip(),
        **assistidos_choices_para_filtros(),
    }
    return render(request, "operacoes/consultas/socioeconomico_print.html", contexto)


# =========================
# ASSISTIDOS — Saúde
# =========================

@login_required
def saude_lista(request):
    if not pode_ver(request.user):
        return HttpResponseForbidden("Sem permissão.")

    qs = assistidos_saude_qs(
        q=request.GET.get("q", ""),
        status=request.GET.get("status", ""),
        diabetes=request.GET.get("diabetes", ""),
        pressao_alta=request.GET.get("pressao_alta", ""),
        medic_uso_continuo=request.GET.get("medic_uso_continuo", ""),
        doenca_permanente=request.GET.get("doenca_permanente", ""),
        order=request.GET.get("o", "nome"),
    )

    contexto = {
        "assistidos": qs,
        "total": qs.count(),
        "q": (request.GET.get("q") or "").strip(),
        "status": (request.GET.get("status") or "").strip(),
        "diabetes": (request.GET.get("diabetes") or "").strip(),
        "pressao_alta": (request.GET.get("pressao_alta") or "").strip(),
        "medic_uso_continuo": (request.GET.get("medic_uso_continuo") or "").strip(),
        "doenca_permanente": (request.GET.get("doenca_permanente") or "").strip(),
        "o": (request.GET.get("o") or "nome").strip(),
        **assistidos_choices_para_filtros(),
    }
    return render(request, "operacoes/consultas/saude_lista.html", contexto)


@login_required
def saude_print(request):
    if not pode_ver(request.user):
        return HttpResponseForbidden("Sem permissão.")

    qs = assistidos_saude_qs(
        q=request.GET.get("q", ""),
        status=request.GET.get("status", ""),
        diabetes=request.GET.get("diabetes", ""),
        pressao_alta=request.GET.get("pressao_alta", ""),
        medic_uso_continuo=request.GET.get("medic_uso_continuo", ""),
        doenca_permanente=request.GET.get("doenca_permanente", ""),
        order=request.GET.get("o", "nome"),
    )

    contexto = {
        "assistidos": qs,
        "total": qs.count(),
        "q": (request.GET.get("q") or "").strip(),
        "status": (request.GET.get("status") or "").strip(),
        "diabetes": (request.GET.get("diabetes") or "").strip(),
        "pressao_alta": (request.GET.get("pressao_alta") or "").strip(),
        "medic_uso_continuo": (request.GET.get("medic_uso_continuo") or "").strip(),
        "doenca_permanente": (request.GET.get("doenca_permanente") or "").strip(),
        "o": (request.GET.get("o") or "nome").strip(),
        **assistidos_choices_para_filtros(),
    }
    return render(request, "operacoes/consultas/saude_print.html", contexto)


# =========================
# BENEFÍCIOS — Atribuições (agrupado por assistido)
# =========================

@login_required
def atribuicoes_consulta(request):
    if not pode_ver(request.user):
        return HttpResponseForbidden("Sem permissão.")

    status = (request.GET.get("status") or "todos").strip().lower()
    q = (request.GET.get("q") or "").strip()

    qs = atribuicoes_qs(q=q, status=status, order_by="assistido__nome")

    grupos = {}
    for a in qs:
        grupos.setdefault(a.assistido, []).append(a)

    contexto = {
        "grupos": grupos,
        "status": status,
        "q": q,
        "total": qs.count(),
    }
    return render(request, "operacoes/consultas/atribuicoes_consulta_lista.html", contexto)


@login_required
def atribuicoes_consulta_print(request):
    if not pode_ver(request.user):
        return HttpResponseForbidden("Sem permissão.")

    status = (request.GET.get("status") or "todos").strip().lower()
    q = (request.GET.get("q") or "").strip()

    qs = atribuicoes_qs(q=q, status=status, order_by="assistido__nome")

    grupos = {}
    for a in qs:
        grupos.setdefault(a.assistido, []).append(a)

    contexto = {
        "grupos": grupos,
        "status": status,
        "q": q,
        "total": qs.count(),
    }
    return render(request, "operacoes/consultas/atribuicoes_consulta_print.html", contexto)


# =========================
# BENEFÍCIOS — Assistidos por benefício
# =========================

ORDERS_BENEFICIO_ASSISTIDOS = {
    "assistido__nome": "assistido__nome",
    "-assistido__nome": "-assistido__nome",
    "data_inicio": "data_inicio",
    "-data_inicio": "-data_inicio",
    "data_termino": "data_termino",
    "-data_termino": "-data_termino",
}


def _get_order_beneficio_assistidos(request):
    raw = (request.GET.get("o") or "assistido__nome").strip()
    return ORDERS_BENEFICIO_ASSISTIDOS.get(raw, "assistido__nome")


@login_required
def beneficio_assistidos_consulta(request):
    if not pode_ver(request.user):
        return HttpResponseForbidden("Sem permissão.")

    beneficio_id = (request.GET.get("beneficio_id") or "").strip()
    status = (request.GET.get("status") or "ativos").strip().lower()
    order = _get_order_beneficio_assistidos(request)

    beneficios = beneficios_com_contadores()
    qs = beneficio_assistidos_qs(beneficio_id=beneficio_id, status=status, order_by=order)

    contexto = {
        "beneficios": beneficios,
        "beneficio_id": beneficio_id,
        "status": status,
        "atribuicoes": qs,
        "total": qs.count(),
        "o": (request.GET.get("o") or "assistido__nome").strip(),
    }
    return render(request, "operacoes/consultas/beneficio_assistidos_lista.html", contexto)


@login_required
def beneficio_assistidos_print(request):
    if not pode_ver(request.user):
        return HttpResponseForbidden("Sem permissão.")

    beneficio_id = (request.GET.get("beneficio_id") or "").strip()
    status = (request.GET.get("status") or "ativos").strip().lower()
    order = _get_order_beneficio_assistidos(request)

    beneficios = beneficios_com_contadores()
    qs = beneficio_assistidos_qs(beneficio_id=beneficio_id, status=status, order_by=order)

    beneficio_sel = None
    if beneficio_id:
        beneficio_sel = Beneficio.objects.filter(id=beneficio_id).first()

    contexto = {
        "beneficios": beneficios,
        "beneficio_id": beneficio_id,
        "beneficio_sel": beneficio_sel,
        "status": status,
        "atribuicoes": qs,
        "total": qs.count(),
        "o": (request.GET.get("o") or "assistido__nome").strip(),
    }
    return render(request, "operacoes/consultas/beneficio_assistidos_print.html", contexto)


# =========================
# ENTREGAS — Lotes (resumo)
# =========================

@login_required
def entregas_lotes_lista(request):
    if not pode_ver(request.user):
        return HttpResponseForbidden("Sem permissão.")

    data_ini = (request.GET.get("data_ini") or "").strip()
    data_fim = (request.GET.get("data_fim") or "").strip()
    beneficio_id = (request.GET.get("beneficio_id") or "").strip()
    order = _get_order_entregas_lotes(request)

    qs = lotes_com_resumo(
        data_ini=data_ini,
        data_fim=data_fim,
        beneficio_id=beneficio_id,
        order_by=order,
    )

    contexto = {
        "lotes": qs,
        "total": qs.count(),
        "beneficios": opcoes_beneficios(),
        "beneficio_id": beneficio_id,
        "data_ini": data_ini,
        "data_fim": data_fim,
        "o": (request.GET.get("o") or "-data_entrega").strip(),
    }
    return render(request, "operacoes/consultas/entregas_lotes_lista.html", contexto)


@login_required
def entregas_lotes_print(request):
    if not pode_ver(request.user):
        return HttpResponseForbidden("Sem permissão.")

    data_ini = (request.GET.get("data_ini") or "").strip()
    data_fim = (request.GET.get("data_fim") or "").strip()
    beneficio_id = (request.GET.get("beneficio_id") or "").strip()
    order = _get_order_entregas_lotes(request)

    qs = lotes_com_resumo(
        data_ini=data_ini,
        data_fim=data_fim,
        beneficio_id=beneficio_id,
        order_by=order,
    )

    beneficio_sel = None
    if beneficio_id:
        beneficio_sel = Beneficio.objects.filter(id=beneficio_id).first()

    contexto = {
        "lotes": qs,
        "total": qs.count(),
        "beneficio_sel": beneficio_sel,
        "beneficio_id": beneficio_id,
        "data_ini": data_ini,
        "data_fim": data_fim,
        "o": (request.GET.get("o") or "-data_entrega").strip(),
    }
    return render(request, "operacoes/consultas/entregas_lotes_print.html", contexto)


# =========================
# ENTREGAS — Itens de um lote (detalhe)
# =========================

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
        "o": (request.GET.get("o") or "atribuicao__assistido__nome").strip(),
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
        "o": (request.GET.get("o") or "atribuicao__assistido__nome").strip(),
    }
    return render(request, "operacoes/consultas/entregas_lote_detalhe_print.html", contexto)


# =========================
# ENTREGAS — Histórico por assistido (itens)
# =========================

@login_required
def entregas_assistido_historico(request):
    if not pode_ver(request.user):
        return HttpResponseForbidden("Sem permissão.")

    q = (request.GET.get("q") or "").strip()
    data_ini = (request.GET.get("data_ini") or "").strip()
    data_fim = (request.GET.get("data_fim") or "").strip()
    beneficio_id = (request.GET.get("beneficio_id") or "").strip()
    status = (request.GET.get("status") or "todos").strip().lower()

    order = _get_order_entregas_assistido(request)

    qs = historico_itens_por_assistido(
        q=q,
        data_ini=data_ini,
        data_fim=data_fim,
        beneficio_id=beneficio_id,
        status=status,
    ).order_by(order)

    contexto = {
        "q": q,
        "data_ini": data_ini,
        "data_fim": data_fim,
        "beneficio_id": beneficio_id,
        "status": status,
        "beneficios": opcoes_beneficios(),
        "itens": qs,
        "total": qs.count(),
        "entregues_count": qs.filter(entregue=True).count(),
        "pendentes_count": qs.filter(entregue=False).count(),
        "o": (request.GET.get("o") or "-lote__data_entrega").strip(),
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

    order = _get_order_entregas_assistido(request)

    qs = historico_itens_por_assistido(
        q=q,
        data_ini=data_ini,
        data_fim=data_fim,
        beneficio_id=beneficio_id,
        status=status,
    ).order_by(order)

    contexto = {
        "q": q,
        "data_ini": data_ini,
        "data_fim": data_fim,
        "beneficio_id": beneficio_id,
        "status": status,
        "beneficios": opcoes_beneficios(),
        "itens": qs,
        "total": qs.count(),
        "entregues_count": qs.filter(entregue=True).count(),
        "pendentes_count": qs.filter(entregue=False).count(),
        "o": (request.GET.get("o") or "-lote__data_entrega").strip(),
    }
    return render(request, "operacoes/consultas/entregas_assistido_historico_print.html", contexto)


# =========================
# LISTA DE CHAMADA — selecionar lote / imprimir em branco
# =========================

@login_required
def entregas_lote_chamada(request):
    if not pode_ver(request.user):
        return HttpResponseForbidden("Sem permissão.")

    data_ini = (request.GET.get("data_ini") or "").strip()
    data_fim = (request.GET.get("data_fim") or "").strip()
    beneficio_id = (request.GET.get("beneficio_id") or "").strip()

    # reaproveita o mesmo resumo (já vem com total/entregues/pendentes)
    lotes = lotes_com_resumo(
        data_ini=data_ini,
        data_fim=data_fim,
        beneficio_id=beneficio_id,
        order_by="-data_entrega",
    )

    context = {
        "lotes": lotes,
        "beneficios": opcoes_beneficios(),
        "data_ini": data_ini,
        "data_fim": data_fim,
        "beneficio_id": beneficio_id,
        "total": lotes.count(),
    }
    return render(request, "operacoes/consultas/entregas_lote_chamada.html", context)


@login_required
def entregas_lote_chamada_print(request):
    if not pode_ver(request.user):
        return HttpResponseForbidden("Sem permissão.")

    lote_id = (request.GET.get("lote_id") or "").strip()
    try:
        lote_int = int(lote_id)
    except (TypeError, ValueError):
        messages.error(request, "Informe um lote válido para imprimir a lista de chamada.")
        return redirect("consultas:entregas_lote_chamada")

    lote = get_object_or_404(LoteEntrega.objects.select_related("beneficio"), id=lote_int)

    itens_qs = (
        ItemEntrega.objects
        .select_related("atribuicao__assistido")
        .filter(lote=lote)
        .order_by("atribuicao__assistido__nome")
    )

    context = {
        "lote": lote,
        "itens": itens_qs,
        "total": itens_qs.count(),
    }
    return render(request, "operacoes/consultas/entregas_lote_chamada_print.html", context)


# =========================
# (Opcional) Resumo em template alternativo
# =========================

@login_required
def consulta_lotes_resumo(request):
    """
    Mantido apenas se você já tiver esse menu/URL.
    Internamente é igual ao 'entregas_lotes_lista', só muda o template.
    """
    if not pode_ver(request.user):
        return HttpResponseForbidden("Sem permissão.")

    beneficio_id = (request.GET.get("beneficio_id") or "").strip()
    data_ini = (request.GET.get("data_ini") or "").strip()
    data_fim = (request.GET.get("data_fim") or "").strip()

    qs = lotes_com_resumo(
        data_ini=data_ini,
        data_fim=data_fim,
        beneficio_id=beneficio_id,
        order_by="-data_entrega",
    )

    return render(
        request,
        "operacoes/consultas/lotes_resumo.html",
        {
            "lotes": qs,
            "beneficios": opcoes_beneficios(),
            "beneficio_id": beneficio_id,
            "data_ini": data_ini,
            "data_fim": data_fim,
        },
    )

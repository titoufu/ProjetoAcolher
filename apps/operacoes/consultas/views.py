from urllib import request
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.db.models import Count, Q
from django.shortcuts import render

from apps.assistidos.models import Assistido
from apps.operacoes.permissoes import pode_ver
 
from django.http import HttpResponseForbidden
from apps.beneficios.models import Beneficio, BeneficioAssistido, LoteEntrega, ItemEntrega

from datetime import date
from django.utils.dateparse import parse_date
from django.shortcuts import get_object_or_404


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



def _aplicar_filtros_e_ordenacao(request):
    """
    Centraliza a lógica de filtros e ordenação para:
    - lista normal (com paginação depois)
    - impressão (sem paginação)
    """
    qs = Assistido.objects.all()

    # ---- filtros (GET) ----
    q = (request.GET.get("q") or "").strip()
    status = (request.GET.get("status") or "").strip()
    logradouro = (request.GET.get("logradouro") or "").strip()
    cep = (request.GET.get("cep") or "").strip()

    if q:
        qs = qs.filter(
            Q(nome__icontains=q)
            | Q(cpf__icontains=q)
            | Q(telefone__icontains=q)
        )

    if status in ["ATIVO", "INATIVO"]:
        qs = qs.filter(status=status)

    if logradouro:
        qs = qs.filter(logradouro__icontains=logradouro)

    if cep:
        # tira traço pra facilitar (opcional)
        cep_clean = cep.replace("-", "").strip()
        qs = qs.filter(cep__icontains=cep_clean)

    # ---- ordenação (GET) ----
    # Permitidas: nome, status, cep, logradouro
    o = (request.GET.get("o") or "nome").strip()
    permitidas = {"nome", "status", "cep", "logradouro"}
    campo = o.lstrip("-")
    if campo not in permitidas:
        o = "nome"

    qs = qs.order_by(o)

    return qs


@login_required
def identificacao_lista(request):
    if not pode_ver(request.user):
        return HttpResponse("Sem permissão.", status=403)

    qs = _aplicar_filtros_e_ordenacao(request)

    # Por enquanto sem template (teste rápido)
    total = qs.count()
    return render(
    request,"operacoes/consultas/identificacao_lista.html",{"assistidos": qs, "total": qs.count(),})

@login_required
def identificacao_print(request):
    if not pode_ver(request.user):
        return HttpResponse("Sem permissão.", status=403)

    qs = _aplicar_filtros_e_ordenacao(request)

    return render(
        request,
        "operacoes/consultas/identificacao_print.html",
        {
            "assistidos": qs,
            "total": qs.count(),
        },
    )
@login_required
def socioeconomico_lista(request):
    if not pode_ver(request.user):
        return HttpResponse("Sem permissão.", status=403)

    qs = Assistido.objects.all()

    # ---- filtros ----
    q = (request.GET.get("q") or "").strip()
    status = (request.GET.get("status") or "").strip()
    sit_trabalho = (request.GET.get("sit_trabalho") or "").strip()
    faixa_renda = (request.GET.get("faixa_renda") or "").strip()
    tipo_moradia = (request.GET.get("tipo_moradia") or "").strip()
    area_risco = (request.GET.get("area_risco") or "").strip()
    escolaridade = (request.GET.get("escolaridade") or "").strip()


    if q:
        qs = qs.filter(
            Q(nome__icontains=q)
            | Q(cpf__icontains=q)
            | Q(telefone__icontains=q)
        )

    if status in ["ATIVO", "INATIVO"]:
        qs = qs.filter(status=status)

    if sit_trabalho:
        qs = qs.filter(sit_trabalho=sit_trabalho)

    if faixa_renda:
        qs = qs.filter(faixa_renda=faixa_renda)

    if tipo_moradia:
        qs = qs.filter(tipo_moradia=tipo_moradia)

    if area_risco:
        qs = qs.filter(area_risco=area_risco)
    
    if escolaridade:
        qs = qs.filter(escolaridade=escolaridade)

    # ---- ordenação ----
    o = (request.GET.get("o") or "nome").strip()
    permitidas = {
        "nome",
        "sit_trabalho",
        "faixa_renda",
        "tipo_moradia",
        "escolaridade",
    }

    campo = o.lstrip("-")
    if campo not in permitidas:
        o = "nome"

    qs = qs.order_by(o)

    return render(
    request,
    "operacoes/consultas/socioeconomico_lista.html",
    {
        "assistidos": qs,
        "total": qs.count(),
        "choices_sit_trabalho": Assistido._meta.get_field("sit_trabalho").choices,
        "choices_faixa_renda": Assistido._meta.get_field("faixa_renda").choices,
        "choices_tipo_moradia": Assistido._meta.get_field("tipo_moradia").choices,
        "choices_area_risco": Assistido._meta.get_field("area_risco").choices,
        "choices_escolaridade": Assistido._meta.get_field("escolaridade").choices,
    },
)


@login_required
def socioeconomico_print(request):
    if not pode_ver(request.user):
        return HttpResponse("Sem permissão.", status=403)

    # reaplica os mesmos filtros manualmente
    qs = Assistido.objects.all()

    q = (request.GET.get("q") or "").strip()
    status = (request.GET.get("status") or "").strip()
    sit_trabalho = (request.GET.get("sit_trabalho") or "").strip()
    faixa_renda = (request.GET.get("faixa_renda") or "").strip()
    tipo_moradia = (request.GET.get("tipo_moradia") or "").strip()
    area_risco = (request.GET.get("area_risco") or "").strip()
    escolaridade = (request.GET.get("escolaridade") or "").strip()


    if q:
        qs = qs.filter(
            Q(nome__icontains=q)
            | Q(cpf__icontains=q)
            | Q(telefone__icontains=q)
        )

    if status in ["ATIVO", "INATIVO"]:
        qs = qs.filter(status=status)

    if sit_trabalho:
        qs = qs.filter(sit_trabalho=sit_trabalho)

    if faixa_renda:
        qs = qs.filter(faixa_renda=faixa_renda)

    if tipo_moradia:
        qs = qs.filter(tipo_moradia=tipo_moradia)

    if area_risco:
        qs = qs.filter(area_risco=area_risco)
    
    if escolaridade:
        qs = qs.filter(escolaridade=escolaridade)


    o = (request.GET.get("o") or "nome").strip()
    permitidas = {
        "nome",
        "sit_trabalho",
        "faixa_renda",
        "tipo_moradia",
        "escolaridade",
    }

    campo = o.lstrip("-")
    if campo not in permitidas:
        o = "nome"

    qs = qs.order_by(o)

    return render(
        request,
        "operacoes/consultas/socioeconomico_print.html",
        {
            "assistidos": qs,
            "choices_escolaridade": Assistido._meta.get_field("escolaridade").choices,
            "total": qs.count(),
        },
    )

@login_required
def saude_lista(request):
    if not pode_ver(request.user):
        return HttpResponse("Sem permissão.", status=403)

    qs = Assistido.objects.all()

    # ---- filtros ----
    q = (request.GET.get("q") or "").strip()
    status = (request.GET.get("status") or "").strip()
    diabetes = (request.GET.get("diabetes") or "").strip()
    pressao_alta = (request.GET.get("pressao_alta") or "").strip()
    medic_uso_continuo = (request.GET.get("medic_uso_continuo") or "").strip()
    doenca_permanente = (request.GET.get("doenca_permanente") or "").strip()

    if q:
        qs = qs.filter(
            Q(nome__icontains=q) |
            Q(cpf__icontains=q) |
            Q(telefone__icontains=q)
        )

    if status in ["ATIVO", "INATIVO"]:
        qs = qs.filter(status=status)

    if diabetes:
        qs = qs.filter(diabetes=diabetes)

    if pressao_alta:
        qs = qs.filter(pressao_alta=pressao_alta)

    if medic_uso_continuo:
        qs = qs.filter(medic_uso_continuo=medic_uso_continuo)

    if doenca_permanente:
        qs = qs.filter(doenca_permanente=doenca_permanente)

    # ---- ordenação ----
    o = (request.GET.get("o") or "nome").strip()
    permitidas = {"nome", "diabetes", "pressao_alta", "medic_uso_continuo", "doenca_permanente"}
    campo = o.lstrip("-")
    if campo not in permitidas:
        o = "nome"
    qs = qs.order_by(o)

    return render(
        request,
        "operacoes/consultas/saude_lista.html",
        {
            "assistidos": qs,
            "total": qs.count(),
            "choices_diabetes": Assistido._meta.get_field("diabetes").choices,
            "choices_pressao_alta": Assistido._meta.get_field("pressao_alta").choices,
            "choices_medic_uso_continuo": Assistido._meta.get_field("medic_uso_continuo").choices,
            "choices_doenca_permanente": Assistido._meta.get_field("doenca_permanente").choices,
        },
    )


@login_required
def saude_print(request):
    if not pode_ver(request.user):
        return HttpResponse("Sem permissão.", status=403)

    qs = Assistido.objects.all()

    q = (request.GET.get("q") or "").strip()
    status = (request.GET.get("status") or "").strip()
    diabetes = (request.GET.get("diabetes") or "").strip()
    pressao_alta = (request.GET.get("pressao_alta") or "").strip()
    medic_uso_continuo = (request.GET.get("medic_uso_continuo") or "").strip()
    doenca_permanente = (request.GET.get("doenca_permanente") or "").strip()

    if q:
        qs = qs.filter(
            Q(nome__icontains=q) |
            Q(cpf__icontains=q) |
            Q(telefone__icontains=q)
        )

    if status in ["ATIVO", "INATIVO"]:
        qs = qs.filter(status=status)

    if diabetes:
        qs = qs.filter(diabetes=diabetes)
    if pressao_alta:
        qs = qs.filter(pressao_alta=pressao_alta)
    if medic_uso_continuo:
        qs = qs.filter(medic_uso_continuo=medic_uso_continuo)
    if doenca_permanente:
        qs = qs.filter(doenca_permanente=doenca_permanente)

    o = (request.GET.get("o") or "nome").strip()
    permitidas = {"nome", "diabetes", "pressao_alta", "medic_uso_continuo", "doenca_permanente"}
    campo = o.lstrip("-")
    if campo not in permitidas:
        o = "nome"
    qs = qs.order_by(o)

    return render(
        request,
        "operacoes/consultas/saude_print.html",
        {
            "assistidos": qs,
            "total": qs.count(),
        },
    )


@login_required
def atribuicoes_consulta(request):
    if not pode_ver(request.user):
        return HttpResponseForbidden("Sem permissão.")

    # filtros (GET)
    status = (request.GET.get("status") or "todos").strip().lower()
    q = (request.GET.get("q") or "").strip()

    qs = (
        BeneficioAssistido.objects
        .select_related("assistido", "beneficio")
        .order_by("assistido__nome", "beneficio__nome")
    )

    # filtro status da atribuição
    if status == "ativos":
        qs = qs.filter(ativo=True)
    elif status == "encerrados":
        qs = qs.filter(ativo=False)
    else:
        status = "todos"  # normaliza

    # filtro texto (nome / cpf)
    if q:
        qs = qs.filter(
            assistido__nome__icontains=q
        ) | qs.filter(
            assistido__cpf__icontains=q
        )

    # agrupar por assistido
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
        qs = qs.filter(
            assistido__nome__icontains=q
        ) | qs.filter(
            assistido__cpf__icontains=q
        )

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
    status = (request.GET.get("status") or "ativos").strip().lower()  # default
    order = _get_order_beneficio_assistidos(request)

    # Benefícios para o select, já com contadores (por benefício)
    beneficios = (
        Beneficio.objects
        .annotate(
            ativos_count=Count(
                "assistidos_atribuidos",
                filter=Q(assistidos_atribuidos__ativo=True),
            ),
            encerrados_count=Count(
                "assistidos_atribuidos",
                filter=Q(assistidos_atribuidos__ativo=False),
            ),
        )
        .order_by("nome", "id")
    )

    # Query base (atribuições)
    qs = (
        BeneficioAssistido.objects
        .select_related("assistido", "beneficio")
        .order_by(order)
    )

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

    # (opcional) se quiser manter o mesmo select no print:
    beneficios = (
        Beneficio.objects
        .annotate(
            ativos_count=Count(
                "assistidos_atribuidos",
                filter=Q(assistidos_atribuidos__ativo=True),
            ),
            encerrados_count=Count(
                "assistidos_atribuidos",
                filter=Q(assistidos_atribuidos__ativo=False),
            ),
        )
        .order_by("nome", "id")
    )

    qs = (
        BeneficioAssistido.objects
        .select_related("assistido", "beneficio")
        .order_by(order)
    )

    if beneficio_id:
        qs = qs.filter(beneficio_id=beneficio_id)

    if status == "ativos":
        qs = qs.filter(ativo=True)
    elif status == "encerrados":
        qs = qs.filter(ativo=False)
    else:
        status = "todos"

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
    }
    return render(request, "operacoes/consultas/beneficio_assistidos_print.html", contexto)

@login_required
def entregas_lotes_lista(request):
    if not pode_ver(request.user):
        return HttpResponseForbidden("Sem permissão.")

    # --- filtros (GET) ---
    data_ini = (request.GET.get("data_ini") or "").strip()
    data_fim = (request.GET.get("data_fim") or "").strip()
    beneficio_id = (request.GET.get("beneficio_id") or "").strip()

    dt_ini = parse_date(data_ini) if data_ini else None
    dt_fim = parse_date(data_fim) if data_fim else None

    order = _get_order_entregas_lotes(request)

    # --- queryset base ---
    qs = (
        LoteEntrega.objects
        .select_related("beneficio")
        .annotate(
            total=Count("itens"),
            entregues=Count("itens", filter=Q(itens__entregue=True)),
            pendentes=Count("itens", filter=Q(itens__entregue=False)),
        )
    )

    # --- aplica filtros ---
    if dt_ini:
        qs = qs.filter(data_entrega__gte=dt_ini)

    if dt_fim:
        qs = qs.filter(data_entrega__lte=dt_fim)

    if beneficio_id:
        qs = qs.filter(beneficio_id=beneficio_id)

    # --- ordenação ---
    qs = qs.order_by(order)

    # dropdown benefícios (para filtro)
    # (se Beneficio já existe em consultas, use o mesmo import que você usa lá)
    beneficios = Beneficio.objects.order_by("nome", "id")

    contexto = {
        "lotes": qs,
        "total": qs.count(),  # total de lotes encontrados (não total de itens)
        "beneficios": beneficios,
        "beneficio_id": beneficio_id,
        "data_ini": data_ini,
        "data_fim": data_fim,
    }
    return render(request, "operacoes/consultas/entregas_lotes_lista.html", contexto)

@login_required
def entregas_lotes_print(request):
    if not pode_ver(request.user):
        return HttpResponseForbidden("Sem permissão.")

    data_ini = (request.GET.get("data_ini") or "").strip()
    data_fim = (request.GET.get("data_fim") or "").strip()
    beneficio_id = (request.GET.get("beneficio_id") or "").strip()

    dt_ini = parse_date(data_ini) if data_ini else None
    dt_fim = parse_date(data_fim) if data_fim else None

    order = _get_order_entregas_lotes(request)

    qs = (
        LoteEntrega.objects
        .select_related("beneficio")
        .annotate(
            total=Count("itens"),
            entregues=Count("itens", filter=Q(itens__entregue=True)),
            pendentes=Count("itens", filter=Q(itens__entregue=False)),
        )
    )

    if dt_ini:
        qs = qs.filter(data_entrega__gte=dt_ini)

    if dt_fim:
        qs = qs.filter(data_entrega__lte=dt_fim)

    if beneficio_id:
        qs = qs.filter(beneficio_id=beneficio_id)

    qs = qs.order_by(order)

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
    }
    return render(request, "operacoes/consultas/entregas_lotes_print.html", contexto)

@login_required
def entregas_lote_detalhe(request):
    if not pode_ver(request.user):
        return HttpResponseForbidden("Sem permissão.")

    lote_id = (request.GET.get("lote_id") or "").strip()
    order = _get_order_entregas_lote(request)

    # agora é obrigatório existir (fluxo vem do "olho")
    lote = get_object_or_404(
        LoteEntrega.objects.select_related("beneficio"),
        id=lote_id
    )

    itens_qs = (
        ItemEntrega.objects
        .select_related("atribuicao__assistido", "atribuicao__beneficio", "lote")
        .filter(lote_id=lote.id)
        .order_by(order)
    )

    entregues = itens_qs.filter(entregue=True)
    pendentes = itens_qs.filter(entregue=False)
    contexto = {
        "lote": lote,
        "itens": itens_qs,              # ✅ compatibilidade
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

    lote = get_object_or_404(
        LoteEntrega.objects.select_related("beneficio"),
        id=lote_id
    )

    itens_qs = (
        ItemEntrega.objects
        .select_related("atribuicao__assistido", "atribuicao__beneficio", "lote")
        .filter(lote_id=lote.id)
        .order_by(order)
    )

    entregues = itens_qs.filter(entregue=True)
    pendentes = itens_qs.filter(entregue=False)

    contexto = {
    "lote": lote,
    "itens": itens_qs,              # ✅ compatibilidade
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

    order = _get_order_entregas_assistido(request)
    

    # select de benefícios (para filtro opcional)
    beneficios = Beneficio.objects.order_by("nome", "id")

    # base: itens de entrega com joins
    qs = (
        ItemEntrega.objects
        .select_related(
            "lote",
            "lote__beneficio",
            "atribuicao",
            "atribuicao__assistido",
        )
    )

    # --- filtro por assistido (q) ---
    if q:
        qs = qs.filter(
            Q(atribuicao__assistido__nome__icontains=q) |
            Q(atribuicao__assistido__cpf__icontains=q) |
            Q(atribuicao__assistido__telefone__icontains=q)
        )
        qs = qs.order_by(order)
    # --- filtro por período (data do lote) ---
    if data_ini:
        qs = qs.filter(lote__data_entrega__gte=data_ini)
    if data_fim:
        qs = qs.filter(lote__data_entrega__lte=data_fim)

    # --- filtro por benefício ---
    if beneficio_id:
        qs = qs.filter(lote__beneficio_id=beneficio_id)

    # --- filtro por status de entrega ---
    if status == "entregues":
        qs = qs.filter(entregue=True)
    elif status == "pendentes":
        qs = qs.filter(entregue=False)
    else:
        status = "todos"

    qs = qs.order_by(order)

    total = qs.count()
    entregues_count = qs.filter(entregue=True).count()
    pendentes_count = qs.filter(entregue=False).count()

    contexto = {
        "q": q,
        "data_ini": data_ini,
        "data_fim": data_fim,
        "beneficio_id": beneficio_id,
        "status": status,

        "beneficios": beneficios,

        "itens": qs,
        "total": total,
        "entregues_count": entregues_count,
        "pendentes_count": pendentes_count,
    }
    return render(
        request,
        "operacoes/consultas/entregas_assistido_historico.html",
        contexto
    )


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
    

    beneficios = Beneficio.objects.order_by("nome", "id")

    qs = (
        ItemEntrega.objects
        .select_related(
            "lote",
            "lote__beneficio",
            "atribuicao",
            "atribuicao__assistido",
        )
    )
    qs = qs.order_by(order)
    if q:
        qs = qs.filter(
            Q(atribuicao__assistido__nome__icontains=q) |
            Q(atribuicao__assistido__cpf__icontains=q) |
            Q(atribuicao__assistido__telefone__icontains=q)
        )

    if data_ini:
        qs = qs.filter(lote__data_entrega__gte=data_ini)
    if data_fim:
        qs = qs.filter(lote__data_entrega__lte=data_fim)

    if beneficio_id:
        qs = qs.filter(lote__beneficio_id=beneficio_id)

    if status == "entregues":
        qs = qs.filter(entregue=True)
    elif status == "pendentes":
        qs = qs.filter(entregue=False)
    else:
        status = "todos"

    qs = qs.order_by(order)

    contexto = {
        "q": q,
        "data_ini": data_ini,
        "data_fim": data_fim,
        "beneficio_id": beneficio_id,
        "status": status,
        "beneficios": beneficios,
        "itens": qs,
        "total": qs.count(),
        "entregues_count": qs.filter(entregue=True).count(),
        "pendentes_count": qs.filter(entregue=False).count(),
    }
    return render(
        request,
        "operacoes/consultas/entregas_assistido_historico_print.html",
        contexto
    )

@login_required
def entregas_lote_chamada(request):
    if not pode_ver(request.user):
        return HttpResponseForbidden("Sem permissão.")

    data_ini = (request.GET.get("data_ini") or "").strip()
    data_fim = (request.GET.get("data_fim") or "").strip()
    beneficio_id = (request.GET.get("beneficio_id") or "").strip()

    lotes = (
        LoteEntrega.objects
        .select_related("beneficio")
        .order_by("-data_entrega", "-id")
    )

    if data_ini:
        lotes = lotes.filter(data_entrega__gte=data_ini)
    if data_fim:
        lotes = lotes.filter(data_entrega__lte=data_fim)
    if beneficio_id:
        lotes = lotes.filter(beneficio_id=beneficio_id)

    # montar contagens (igual seu padrão de lotes)
    lotes_list = []
    for l in lotes:
        total = ItemEntrega.objects.filter(lote=l).count()
        entregues = ItemEntrega.objects.filter(lote=l, entregue=True).count()
        pendentes = total - entregues
        l.total = total
        l.entregues = entregues
        l.pendentes = pendentes
        lotes_list.append(l)

    beneficios = Beneficio.objects.order_by("nome", "id")

    context = {
        "lotes": lotes_list,
        "beneficios": beneficios,
        "data_ini": data_ini,
        "data_fim": data_fim,
        "beneficio_id": beneficio_id,
        "total": len(lotes_list),
    }
    return render(request, "operacoes/consultas/entregas_lote_chamada.html", context)

@login_required
def entregas_lote_chamada_print(request):
    if not pode_ver(request.user):
        return HttpResponseForbidden("Sem permissão.")

    lote_id = (request.GET.get("lote_id") or "").strip()
    if not lote_id.isdigit():
        messages.error(request, "Informe um lote válido para imprimir a lista de chamada.")
        return redirect("consultas:entregas_lote_chamada")

    lote = get_object_or_404(
        LoteEntrega.objects.select_related("beneficio"),
        id=int(lote_id)
    )

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
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q
from django.shortcuts import render

from apps.beneficios.models import LoteEntrega, Beneficio


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

    return render(
        request,
        "operacoes/consultas/lotes_resumo.html",
        {
            "lotes": qs,
            "beneficios": beneficios,
            "beneficio_id": beneficio_id,
            "data_ini": data_ini,
            "data_fim": data_fim,
            "campo_data": campo_data,
        },
    )


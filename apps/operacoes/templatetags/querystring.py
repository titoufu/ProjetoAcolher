from urllib.parse import urlencode

from django import template

register = template.Library()


@register.simple_tag
def qs_update(request, **kwargs):
    """
    Retorna a querystring atual, atualizando/substituindo parâmetros.

    - Preserva todos os parâmetros existentes (filtros, paginação, etc.)
    - Substitui os parâmetros passados em kwargs
    - Remove parâmetros cujo valor seja "" ou None
    """
    params = request.GET.copy()

    for key, value in kwargs.items():
        if value is None or value == "":
            params.pop(key, None)
        else:
            params[key] = str(value)

    query = params.urlencode()
    return query


@register.simple_tag
def sort_qs(request, field, default_field="nome"):
    """
    Alterna ordenação (asc/desc) do campo "field", preservando filtros.

    Regras:
    - Se não há ordenação, usa default_field
    - Se ordenação atual é field -> vira -field
    - Se ordenação atual é -field -> vira field
    - Se ordenação atual é outro campo -> vira field
    Também zera paginação (se existir) para evitar cair em página vazia após reorder.
    """
    current = request.GET.get("o") or default_field

    if current == field:
        new_o = f"-{field}"
    elif current == f"-{field}":
        new_o = field
    else:
        new_o = field

    params = request.GET.copy()
    params["o"] = new_o
    # se você usar paginação depois, é bom resetar:
    params.pop("page", None)

    return params.urlencode()


@register.simple_tag
def sort_icon(request, field, default_field="nome"):
    """
    Retorna um símbolo simples para indicar a ordenação atual:
    ▲ para asc, ▼ para desc, "" se não estiver ordenando por este campo.
    """
    current = request.GET.get("o") or default_field
    if current == field:
        return "▲"
    if current == f"-{field}":
        return "▼"
    return ""

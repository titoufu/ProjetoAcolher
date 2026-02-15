# apps/operacoes/context_processors.py
from .permissoes import pode_ver, pode_editar, pode_deletar

def operacoes_permissoes(request):
    """
    Injeta flags globais de permissão para todos os templates.
    Assim o base.html não precisa adivinhar grupo do usuário.
    """
    user = getattr(request, "user", None)

    if user and user.is_authenticated:
        return {
            "pode_ver": pode_ver(user),
            "pode_editar": pode_editar(user),
            "pode_deletar": pode_deletar(user),
        }

    return {
        "pode_ver": False,
        "pode_editar": False,
        "pode_deletar": False,
    }

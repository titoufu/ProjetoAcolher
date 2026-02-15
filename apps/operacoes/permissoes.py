def is_consultor(user):
    return user.groups.filter(name="Consultor").exists()

def is_supervisor(user):
    return user.groups.filter(name="Supervisor").exists()

def is_operador(user):
    return user.groups.filter(name="Operador").exists()

def pode_ver(user):
    return is_consultor(user) or is_operador(user) or is_supervisor(user) or user.is_superuser

def pode_editar(user):
    return is_operador(user) or is_supervisor(user) or user.is_superuser

def pode_deletar(user):
    return is_supervisor(user) or user.is_superuser


 
from django.contrib.auth.decorators import login_required
from django.shortcuts import render

@login_required
def ficha_inscricao(request):
    return render(request, "impressos/ficha_inscricao_assistido.html")

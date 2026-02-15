from django.shortcuts import render
from .models import Assistido


def assistido_list(request):
    assistidos = Assistido.objects.all()
    return render(
        request,
        "assistidos/assistido_list.html",
        {"assistidos": assistidos},
    )

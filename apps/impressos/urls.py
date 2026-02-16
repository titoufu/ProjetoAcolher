from django.urls import path
from . import views

app_name = "impressos"

urlpatterns = [
    path("ficha-inscricao/", views.ficha_inscricao, name="ficha_inscricao"),
]

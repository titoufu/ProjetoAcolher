from django.contrib import admin
from django.urls import path, include
from django.shortcuts import redirect

def home(request):
    return redirect("/accounts/login/")  # ou "/operacoes/"

urlpatterns = [
    path("", home),
    path("admin/", admin.site.urls),
    path("accounts/", include("django.contrib.auth.urls")),
    path("operacoes/", include("apps.operacoes.urls")),
    path("impressos/", include("apps.impressos.urls")),
]
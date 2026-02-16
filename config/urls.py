from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path("admin/", admin.site.urls),
    path("accounts/", include("django.contrib.auth.urls")),
    path("operacoes/", include("apps.operacoes.urls")),
    path("impressos/", include("apps.impressos.urls")),

]

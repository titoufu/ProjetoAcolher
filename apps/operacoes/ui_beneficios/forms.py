# apps/operacoes/beneficios/forms.py
from django import forms
from apps.beneficios.models import Beneficio

class BeneficioForm(forms.ModelForm):
    class Meta:
        model = Beneficio
        fields = "__all__"

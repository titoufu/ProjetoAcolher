from django import forms
from apps.beneficios.models import LoteEntrega, Beneficio


class LoteEntregaForm(forms.ModelForm):
    class Meta:
        model = LoteEntrega
        fields = ["data_entrega", "beneficio"]
        widgets = {
            "data_entrega": forms.DateInput(attrs={"type": "date", "class": "form-control"}),
            "beneficio": forms.Select(attrs={"class": "form-select"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["beneficio"].queryset = Beneficio.objects.filter(ativo=True)

    # ✅ desliga a validação automática de unicidade do Django (a que gera a msg em inglês)
    def validate_unique(self):
        return

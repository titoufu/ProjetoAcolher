from django import forms
from apps.assistidos.models import Assistido 
from apps.beneficios.models import BeneficioAssistido, Beneficio
from django.db.models import Q

class AssistidoForm(forms.ModelForm):
    # Permite máscara no CPF (14 caracteres)
    cpf = forms.CharField(
        required=False,
        max_length=14,
        label="CPF",
    )

    class Meta:
        model = Assistido
        fields = [
            # Identificação
            "nome", "cpf", "data_nascimento", "telefone",

            # Endereço
            "logradouro", "numero", "complemento", "bairro", "cidade", "uf", "cep",

            # Socioeconômico
            "sit_trabalho", "responsavel_renda", "faixa_renda", "tipo_moradia",
            "material_moradia", "area_risco", "sabe_ler_escrever", "escolaridade",

            # Saúde
            "diabetes", "pressao_alta", "medic_uso_continuo", "doenca_permanente",

            # Programa
            "data_inicio_apoio",

            # Status
            "status", "motivo_inativacao",
        ]

        widgets = {
            "data_nascimento": forms.DateInput(
                attrs={"type": "date", "class": "form-control"},
                format="%Y-%m-%d",
            ),
            "data_inicio_apoio": forms.DateInput(
                attrs={"type": "date", "class": "form-control"},
                format="%Y-%m-%d",
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Date format
        self.fields["data_nascimento"].input_formats = ["%Y-%m-%d"]
        self.fields["data_inicio_apoio"].input_formats = ["%Y-%m-%d"]

        # Ajuste visual CPF (sem travar)
        self.fields["cpf"].widget.attrs.update({
            "class": "form-control",
            "maxlength": "14",
            "placeholder": "000.000.000-00",
            "inputmode": "numeric",
            
        })
            # Ajuste visual TELEFONE
        self.fields["telefone"].widget.attrs.update({
            "placeholder": "(00) 00000-0000",
            "inputmode": "numeric",
            "maxlength": "15",
        })

        # Bootstrap geral
        for name, field in self.fields.items():
            if name in ["cpf", "data_nascimento", "data_inicio_apoio"]:
                continue
            if isinstance(field.widget, forms.Select):
                field.widget.attrs.setdefault("class", "form-select")
            else:
                field.widget.attrs.setdefault("class", "form-control")

    def clean_cpf(self):
        cpf = self.cleaned_data.get("cpf") or ""
        # Remove máscara antes de mandar para o Model
        cpf_digits = "".join(ch for ch in cpf if ch.isdigit())
        return cpf_digits or None
    
    def clean_telefone(self):
        tel = self.cleaned_data.get("telefone") or ""
        tel_digits = "".join(ch for ch in tel if ch.isdigit())
        return tel_digits or ""

from django import forms
from apps.beneficios.models import Beneficio, BeneficioAssistido


class BeneficioAssistidoForm(forms.ModelForm):
    class Meta:
        model = BeneficioAssistido
        fields = ["beneficio", "data_inicio", "data_termino"]
        widgets = {
            "data_inicio": forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d"),
            "data_termino": forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d"),}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # ✅ por padrão: só ativos
        qs = Beneficio.objects.filter(ativo=True)

        # ✅ MAS: se estou editando e o benefício atual é inativo, inclua ele no select
        if self.instance and self.instance.pk and self.instance.beneficio_id:
            qs = Beneficio.objects.filter(Q(ativo=True) | Q(pk=self.instance.beneficio_id))

        self.fields["beneficio"].queryset = qs.order_by("nome")

        # Bootstrap
        for name, field in self.fields.items():
            if isinstance(field.widget, forms.Select):
                field.widget.attrs.setdefault("class", "form-select")
            else:
                field.widget.attrs.setdefault("class", "form-control")

    def clean_beneficio(self):
        beneficio = self.cleaned_data.get("beneficio")
        if not beneficio:
            return beneficio

        # ✅ Regra: não permitir escolher benefício inativo,
        # EXCETO quando estou apenas mantendo o benefício já existente na atribuição.
        if (not beneficio.ativo) and (not self.instance.pk or beneficio.pk != self.instance.beneficio_id):
            raise forms.ValidationError("Este benefício está inativo e não pode ser atribuído.")
        return beneficio
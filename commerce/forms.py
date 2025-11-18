from django import forms
from .models import Invoice
from django.utils.timezone import now


class InvoiceForm(forms.ModelForm):
    class Meta:
        model = Invoice
        fields = [
            "customer",
            "payment_method",
            "issue_date",
            "subtotal",
            "iva",
            "total",
        ]
        widgets = {
            "customer": forms.Select(),
            "payment_method": forms.Select(),
            "issue_date": forms.DateInput(
                attrs={"type": "date"}, format="%Y-%m-%d"  # <- importante
            ),
            "subtotal": forms.NumberInput(),
            "iva": forms.NumberInput(),
            "total": forms.NumberInput(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Si no hay valor, asigna la fecha actual
        if not self.instance.pk:  # Nuevo registro
            self.initial["issue_date"] = now().date()

from django import forms
from .models import Purchase
from django.utils.timezone import now


class PurchaseForm(forms.ModelForm):
    class Meta:
        model = Purchase
        fields = [
            "supplier",
            "num_document",
            "issue_date",
            "subtotal",
            "iva",
            "total",
        ]
        widgets = {
            "supplier": forms.Select(),
            "num_document": forms.TextInput(),
            "issue_date": forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d"),
            "subtotal": forms.NumberInput(),
            "iva": forms.NumberInput(),
            "total": forms.NumberInput(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.instance.pk:
            self.initial["issue_date"] = now().date()

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
            "supplier": forms.Select(attrs={'class': 'form-control'}),
            "num_document": forms.TextInput(attrs={'class': 'form-control'}),
            "issue_date": forms.DateInput(attrs={"type": "date", 'class': 'form-control'}, format='%Y-%m-%d'),
            "subtotal": forms.NumberInput(attrs={'readonly': True, 'class': 'form-control'}),
            "iva": forms.NumberInput(attrs={'readonly': True, 'class': 'form-control'}),
            "total": forms.NumberInput(attrs={'readonly': True, 'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.instance.pk:
            self.initial['issue_date'] = now().date()

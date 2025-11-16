from django import forms
from core.models import Supplier

class SupplierForm(forms.ModelForm):
    class Meta:
        model=Supplier
        fields=['name','ruc','address','phone','state']
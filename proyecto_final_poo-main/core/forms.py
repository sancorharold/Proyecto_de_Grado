from django import forms
from core.models import Supplier, Brand

class SupplierForm(forms.ModelForm):
    class Meta:
        model=Supplier
        fields=['name','ruc','address','phone','state']

class BrandForm(forms.ModelForm):
    class Meta:
        model = Brand
        fields = ['supplier', 'description', 'state']
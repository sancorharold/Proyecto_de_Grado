from .models import Invoice
from django.urls import reverse_lazy
from django import forms

from commerce.models import Invoice
class InvoiceForm(forms.ModelForm):
    class Meta:
        model=Invoice
        fields = ['customer', 'payment_method', 'issue_date', 'subtotal', 'iva', 'total']
        widgets = {
            'customer': forms.Select(),
            'payment_method': forms.Select(),
            'issue_date': forms.DateInput(attrs={'type': 'date'}),
            'subtotal': forms.NumberInput(),
            'iva': forms.NumberInput(),
            'total': forms.NumberInput(),
           
        }
    
    def __init__(self, *args, **kwargs):
        # El 'user' puede no estar presente, por ejemplo, al crear una factura.
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Si el formulario es para una instancia existente (actualización) y el usuario no es superusuario
        if self.instance and self.instance.pk and user and not user.is_superuser:
            # si no es super usuario no puede ingresar fechas de facturacion
            self.fields['issue_date'].widget.attrs['readonly'] = True
            self.fields['issue_date'].widget.attrs['style'] = 'pointer-events: none; background-color: #e9ecef;'
        elif not (self.instance and self.instance.pk): # Si es un formulario de creación
            self.fields.pop('issue_date', None)
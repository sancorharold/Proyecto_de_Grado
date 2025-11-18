from django import forms
from .models import Prestamo, PrestamoDetalle


class PrestamoForm(forms.ModelForm):
    # ... (Tu código actual) ...
    class Meta:
        model = Prestamo
        fields = [
            'empleado', 
            'tipo_prestamo', 
            'fecha_prestamo', 
            'monto', 
            'numero_cuotas'
        ]
        
        # Puedes añadir widgets para mejorar la interfaz de usuario, especialmente para fechas.
        widgets = {
            'empleado': forms.Select(attrs={'class': 'form-control select2'}),
            'tipo_prestamo': forms.Select(attrs={'class': 'form-control select2'}),
            'fecha_prestamo': forms.DateInput(
                format='%Y-%m-%d',
                attrs={
                    'class': 'form-control',
                    'type': 'date' # HTML5 date input
                }
            ),
            'monto': forms.NumberInput(attrs={'class': 'form-control'}),
            'numero_cuotas': forms.NumberInput(attrs={'class': 'form-control'}),
        }
        
    def clean(self):
        """
        Validación adicional del formulario.
        """
        cleaned_data = super().clean()
        monto = cleaned_data.get("monto")
        numero_cuotas = cleaned_data.get("numero_cuotas")
        
        if monto and monto <= 0:
            self.add_error('monto', 'El monto solicitado debe ser mayor que cero.')
            
        if numero_cuotas and numero_cuotas <= 0:
            self.add_error('numero_cuotas', 'El número de cuotas debe ser mayor que cero.')
            
        return cleaned_data


# NOTA IMPORTANTE sobre PrestamoDetalle:
# Generalmente, no se crea un ModelForm para PrestamoDetalle porque:
# 1. Los registros de detalle se crean/actualizan en bloque desde el código (vía form_valid) 
#    utilizando los datos de JSON que envías desde JavaScript (como viste en InvoiceCreateView).
# 2. El modelo PrestamoDetalle está intrínsecamente ligado al Prestamo y su lógica de cálculo.
# Si fuera necesario para un caso de uso muy específico, se definiría aquí.
from django.contrib import admin
# IMPORTAMOS los modelos desde models.py
from .models import TipoPrestamo, Empleado, Prestamo, PrestamoDetalle 

# --- Clases Admin para mejor visualización (Opcional) ---

@admin.register(TipoPrestamo)
class TipoPrestamoAdmin(admin.ModelAdmin):
    list_display = ('descripcion', 'tasa')
    search_fields = ('descripcion',)

@admin.register(Empleado)
class EmpleadoAdmin(admin.ModelAdmin):
    list_display = ('nombres', 'sueldo')
    search_fields = ('nombres',)

# Inline para PrestamoDetalle (permite ver y editar cuotas dentro del formulario de Prestamo)
class PrestamoDetalleInline(admin.TabularInline):
    model = PrestamoDetalle
    extra = 0  # No muestra campos vacíos por defecto
    readonly_fields = ('numero_cuota', 'fecha_vencimiento', 'valor_cuota', 'saldo_cuota')
    # Si quieres evitar que se modifiquen los detalles desde el admin una vez creados:
    can_delete = False
    
@admin.register(Prestamo)
class PrestamoAdmin(admin.ModelAdmin):
    list_display = (
        'id', 
        'empleado', 
        'fecha_prestamo', 
        'monto', 
        'numero_cuotas', 
        'saldo', 
        'estado'
    )
    list_filter = ('estado', 'tipo_prestamo')
    search_fields = ('empleado__nombres', 'id')
    inlines = [PrestamoDetalleInline]
    
    # Campos que el usuario no puede editar manualmente
    readonly_fields = ('interes', 'monto_pagar', 'saldo') 
    
    # Define cómo se agrupan los campos en el formulario
    fieldsets = (
        (None, {
            'fields': ('empleado', 'tipo_prestamo', 'fecha_prestamo', 'estado')
        }),
        ('Detalles Financieros', {
            'fields': ('monto', 'interes', 'monto_pagar', 'numero_cuotas', 'saldo')
        }),
    )
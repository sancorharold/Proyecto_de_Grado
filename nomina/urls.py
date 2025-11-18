from django.urls import path
from .views import (
    PrestamoListView,
    PrestamoCreateView,
    PrestamoUpdateView,
    PrestamoDeleteView,
    PrestamoAnnulView,
    PrestamoDetailView,
    PrestamoPrintView, # Descomenta si usas la vista de impresión
)

# Definimos el nombre de la aplicación para usarlo en el namespace (ej: reverse_lazy('nomina:prestamo_list'))
app_name = 'nomina'

urlpatterns = [
    # 1. Listado de Préstamos
    path(
        'prestamos/', 
        PrestamoListView.as_view(), 
        name='prestamo_list'
    ),
    
    # 2. Creación de Préstamo
    path(
        'prestamos/nuevo/', 
        PrestamoCreateView.as_view(), 
        name='prestamo_create'
    ),
    
    # 3. Edición de Préstamo
    path(
        'prestamos/editar/<int:pk>/', 
        PrestamoUpdateView.as_view(), 
        name='prestamo_update'
    ),
    
    # 4. Detalle de Préstamo (usado generalmente para modales)
    path(
        'prestamos/detalle/<int:pk>/', 
        PrestamoDetailView.as_view(), 
        name='prestamo_detail'
    ),
    
    # 5. Eliminación de Préstamo (vía POST)
    path(
        'prestamos/eliminar/<int:pk>/', 
        PrestamoDeleteView.as_view(), 
        name='prestamo_delete'
    ),
    
    # 6. Anulación de Préstamo (vía POST)
    path(
        'prestamos/anular/<int:pk>/', 
        PrestamoAnnulView.as_view(), 
        name='prestamo_annul'
    ),
    
  
    path(
        'prestamos/imprimir/<int:pk>/', 
        PrestamoPrintView.as_view(), 
        name='prestamo_print' # 🚨 Descomentar esta línea 🚨
    ),
]
import json
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import transaction
from django.urls import reverse_lazy
from django.http import HttpResponse, JsonResponse
from django.views.generic import (
    ListView,
    CreateView,
    UpdateView,
    View,
    DetailView,
)
from django.template.loader import render_to_string # Importación necesaria para PrestamoDetailView
from .forms import PrestamoForm
from core.mixins import TitleContextMixin
from .models import Prestamo, PrestamoDetalle # Asegúrate de que los related_name funcionen
from django.db.models import Sum


# --- Vistas del Modelo Prestamo (Maestro) ---

class PrestamoListView(LoginRequiredMixin, TitleContextMixin, ListView): 
    model = Prestamo
    template_name = "nomina/list.html"
    context_object_name = "prestamos"
    paginate_by = 10
    title2 = "Listado de Préstamos"

# -------------------------------------------------------------
# VISTAS DE CREACIÓN Y EDICIÓN (Manejan AJAX y Detalle JSON)
# -------------------------------------------------------------

class PrestamoCreateView(LoginRequiredMixin, TitleContextMixin, CreateView):
    model = Prestamo
    form_class = PrestamoForm
    template_name = "nomina/form.html"
    success_url = reverse_lazy("nomina:prestamo_list")
    title2 = "Nuevo Préstamo"

    def form_valid(self, form):
        # 1. Obtener y parsear el detalle JSON
        detail_data_json = self.request.POST.get('detail', '[]')
        
        try:
            detail_data = json.loads(detail_data_json)
        except json.JSONDecodeError:
            return JsonResponse({"error": "Formato de detalle de cuotas inválido."}, status=400)

        if not detail_data:
            return JsonResponse({"error": "Debe generar las cuotas del préstamo."}, status=400)
            
        try:
            with transaction.atomic():
                # 2. Guardar el objeto Maestro (Prestamo)
                prestamo = form.save(commit=False)
                # Asignación de campos calculados (si existen en el modelo Prestamo)
                if hasattr(prestamo, 'monto_pagar'):
                    prestamo.monto_pagar = sum(item['valor_cuota'] for item in detail_data)
                
                # Si el modelo tiene un campo 'saldo' que debe reflejar el total
                if hasattr(prestamo, 'saldo'):
                    prestamo.saldo = prestamo.monto_pagar if hasattr(prestamo, 'monto_pagar') else prestamo.monto
                
                prestamo.save() # Guarda la cabecera

                # 3. Crear los objetos PrestamoDetalle en bloque
                detalles_a_crear = [
                    PrestamoDetalle(
                        prestamo=prestamo,
                        numero_cuota=item['numero_cuota'],
                        fecha_vencimiento=item['fecha_vencimiento'],
                        valor_cuota=item['valor_cuota'],
                        # saldo_cuota debe ser el valor completo al inicio
                        saldo_cuota=item['valor_cuota'], 
                    ) for item in detail_data
                ]
                
                PrestamoDetalle.objects.bulk_create(detalles_a_crear)

                return JsonResponse(
                    {"msg": "Préstamo guardado con éxito.", "url": self.success_url}
                )
        except Exception as e:
            return JsonResponse({"error": f"Error al guardar: {str(e)}"}, status=400)


class PrestamoUpdateView(LoginRequiredMixin, TitleContextMixin, UpdateView):
    model = Prestamo
    form_class = PrestamoForm
    template_name = "nomina/form.html"
    success_url = reverse_lazy("nomina:prestamo_list")
    title2 = "Editar Préstamo"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Cargar los detalles existentes
        details = PrestamoDetalle.objects.filter(prestamo=self.object)
        
        context["detail_prestamo"] = json.dumps(
            [
                {
                    "numero_cuota": d.numero_cuota,
                    "fecha_vencimiento": str(d.fecha_vencimiento),
                    "valor_cuota": float(d.valor_cuota),
                    "saldo_cuota": float(d.saldo_cuota),
                }
                for d in details
            ]
        )
        return context

    def form_valid(self, form):
        detail_data_json = self.request.POST.get('detail', '[]')
        
        try:
            detail_data = json.loads(detail_data_json)
        except json.JSONDecodeError:
            return JsonResponse({"error": "Formato de detalle de cuotas inválido."}, status=400)

        if not detail_data:
            return JsonResponse({"error": "Debe generar las cuotas del préstamo."}, status=400)
            
        try:
            with transaction.atomic():
                prestamo = form.save()
                
                # Restricción de edición
                if prestamo.estado == 'PEND':
                    # Eliminar y recrear solo si está Pendiente
                    prestamo.detalles.all().delete() 
                    
                    detalles_a_crear = [
                        PrestamoDetalle(
                            prestamo=prestamo,
                            numero_cuota=item['numero_cuota'],
                            fecha_vencimiento=item['fecha_vencimiento'],
                            valor_cuota=item['valor_cuota'],
                            saldo_cuota=item['valor_cuota'],
                        ) for item in detail_data
                    ]
                    PrestamoDetalle.objects.bulk_create(detalles_a_crear)
                else:
                    # En modo edición, si el estado no es PEND, solo se guardan los campos del maestro (form.save() ya lo hizo)
                    pass # Se omite la recreación de detalles si el estado no es 'PEND'
                    
            return JsonResponse({"msg": "Préstamo actualizado con éxito", "url": self.success_url})
        except Exception as e:
            return JsonResponse({"error": f"Error al actualizar: {str(e)}"}, status=400)


# --- El resto de las vistas (DeleteView, AnnulView, DetailView) ---

class PrestamoDeleteView(LoginRequiredMixin, View):
    def post(self, request, pk, *args, **kwargs):
        try:
            prestamo = Prestamo.objects.get(pk=pk)
            if prestamo.estado == 'PEND' or prestamo.estado == 'ANU': 
                 prestamo.delete()
                 return JsonResponse({"msg": "Préstamo eliminado correctamente."})
            else:
                 return JsonResponse({"error": "No se puede eliminar un préstamo en estado de pago."}, status=400)
        except Prestamo.DoesNotExist:
            return JsonResponse({"error": "Préstamo no encontrado."}, status=404)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=400)


class PrestamoAnnulView(LoginRequiredMixin, View):
    def post(self, request, pk, *args, **kwargs):
        try:
            prestamo = Prestamo.objects.get(pk=pk)
            if prestamo.estado == 'PEND':
                prestamo.estado = 'ANU'
                prestamo.save()
                return JsonResponse({"msg": "Préstamo anulado correctamente."})
            else:
                return JsonResponse({"error": "El préstamo no puede ser anulado en su estado actual."}, status=400)
        except Prestamo.DoesNotExist:
            return JsonResponse({"error": "Préstamo no encontrado."}, status=404)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=400)


class PrestamoDetailView(LoginRequiredMixin, DetailView):
    model = Prestamo
    template_name = "nomina/detail_modal.html"

    def get(self, request, *args, **kwargs):
        prestamo = self.get_object()
        context = {
            "prestamo": prestamo,
            "detalles": prestamo.detalles.all()
        }
        html = render_to_string(self.template_name, context)
        return JsonResponse({"html": html})
    
from django.http import JsonResponse, HttpResponse # Asegúrate de importar HttpResponse

# ... (todas tus clases existentes: PrestamoListView, PrestamoCreateView, etc.) ...

# 🚨 AÑADE ESTA CLASE (si no existe) o DESCOMÉNTALA (si estaba comentada) 🚨
class PrestamoPrintView(LoginRequiredMixin, View):
    """
    Vista para imprimir o generar PDF de un préstamo.
    """
    def get(self, request, pk, *args, **kwargs):
        # Implementación mínima. Reemplazar con lógica real de PDF/impresión.
        try:
            # Asumiendo que tienes Prestamo importado
            prestamo = Prestamo.objects.get(pk=pk)
            return HttpResponse(f"<h1>Imprimiendo Préstamo {prestamo.pk} - {prestamo.empleado}</h1>", content_type="text/html")
        except Prestamo.DoesNotExist:
            return HttpResponse("Préstamo no encontrado.", status=404)
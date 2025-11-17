from django.http import HttpResponse
from django.contrib.auth.mixins import LoginRequiredMixin
from core.mixins import TitleContextMixin
from core.models import Product, Customer
from core.utils import custom_serializer
from .forms import InvoiceForm
from .models import Invoice, InvoiceDetail 
from django.db.models import Q
from django.urls import reverse_lazy
from django.views.generic import CreateView, ListView, UpdateView,DetailView,View
from django.contrib import messages
from django.http import JsonResponse
from decimal import Decimal
from django.utils import timezone
from django.db import transaction
from django.template.loader import render_to_string
import json
from .utils import render_to_pdf # Importar la nueva función

class InvoiceListView(LoginRequiredMixin,TitleContextMixin,ListView): 
    model = Invoice 
    template_name = 'invoice/list.html'  # Nombre del template a usar 
    context_object_name = 'invoices'     # Nombre del contexto a pasar al template 
    paginate_by = 10   
                
    title1 = "Autor | TeacherCode"
    title2 = "Listado de Ventas"

    def get_queryset(self):
        # Se Puede personalizar el queryset aquí si es necesario
        queryset = super().get_queryset()  # self.model.objects.all()
        query = self.request.GET.get('q','')
        if query:
            queryset = queryset.filter(Q(customer__last_name__icontains=query) | Q(customer__first_name__icontains=query))
        return queryset
    
   
class InvoiceCreateView(LoginRequiredMixin,TitleContextMixin,CreateView):
    model = Invoice
    form_class = InvoiceForm
    template_name = "invoice/form.html"
    success_url = reverse_lazy("commerce:invoice_list")  # Redirigir a la lista de proveedores después de crear uno nuevo
    title1 = '"Ventas"'
    title2 = 'Crear Nueva Venta'
          
    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        # Intentar encontrar el cliente "Consumidor Final"
        try:
            generic_customer = Customer.objects.get(dni='9999999999999')
            form.fields['customer'].initial = generic_customer.pk
        except Customer.DoesNotExist:
            # Si no existe, no hacemos nada, el campo aparecerá vacío.
            pass
        return form

    def get_context_data(self, **kwargs):
        context = super().get_context_data()
        context['products'] = Product.active_products.only('id','description','price','stock','iva')
        context['detail_sales'] = json.dumps([]) # Convertir la lista vacía a una cadena JSON '[]'
        context['save_url'] = reverse_lazy('commerce:invoice_create') 
        context['invoice_list_url'] = self.success_url 
        print(context['products'])
        return context
    
    def post(self, request, *args, **kwargs):
        data = request.POST
        form = self.form_class(data)
        
        if form.is_valid():
            try:
                with transaction.atomic():
                    details = json.loads(data['detail'])
                    
                    # --- Cálculo automático de totales ---
                    total_subtotal = sum(Decimal(d['sub']) for d in details)
                    total_iva = sum(Decimal(d['iva']) for d in details)
                    grand_total = total_subtotal + total_iva

                    # Crear la factura desde el formulario pero sin guardarla aún
                    invoice = form.save(commit=False)
                    invoice.user = request.user
                    invoice.issue_date = timezone.now() # Fecha automática
                    invoice.subtotal, invoice.iva, invoice.total = total_subtotal, total_iva, grand_total
                    invoice.save()
                    
                    for detail in details:
                        inv_det = InvoiceDetail.objects.create(
                            invoice=invoice,
                            product_id=int(detail['id']),
                            quantity=Decimal(detail['quantity']),
                            price=Decimal(detail['price']),
                            iva=Decimal(detail['iva']),
                            subtotal=Decimal(detail['sub'])
                        )
                        inv_det.product.reduce_stock(Decimal(detail['quantity']))
                
                    messages.success(self.request, f"Éxito al registrar la venta F#{invoice.id}")
                    return JsonResponse({"msg": "Éxito al registrar la venta Factura"}, status=201)
            except Exception as ex:
                return JsonResponse({"msg": str(ex)}, status=400)
        else:
            messages.error(self.request, f"Error al grabar la venta: {form.errors}")
            return JsonResponse({"msg": form.errors}, status=400)

class InvoiceUpdateView(LoginRequiredMixin,TitleContextMixin,UpdateView):
    model = Invoice
    form_class = InvoiceForm
    template_name = "invoice/form.html"
    success_url = reverse_lazy("commerce:invoice_list")
    title1 = '"Venta"'
    title2 = 'Editar Venta'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['products'] = Product.active_products.only('id','description','price','stock','iva')
        context['invoice_list_url'] = self.success_url
        detail_sale = list(InvoiceDetail.objects.filter(invoice_id=self.object.id).values(
            "product_id", "product__description", "quantity", "price", "subtotal", "iva"))
        
        # Renombrar 'product_id' a 'id' para consistencia con el frontend
        for item in detail_sale:
            item['id'] = item.pop('product_id')

        context['detail_sales'] = json.dumps(detail_sale, default=custom_serializer)
        context['save_url'] = reverse_lazy('commerce:invoice_update', kwargs={"pk": self.object.id})
        return context
    
    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        data = request.POST
        form = self.get_form()

        if form.is_valid():
            with transaction.atomic():
                # Restaurar stock de los detalles antiguos
                old_details = InvoiceDetail.objects.filter(invoice=self.object)
                for det in old_details:
                    det.product.stock += det.quantity
                    det.product.save()
                old_details.delete()

                details = json.loads(request.POST['detail'])

                # --- Recalcular totales para la actualización ---
                total_subtotal = sum(Decimal(d['sub']) for d in details)
                total_iva = sum(Decimal(d['iva']) for d in details)
                grand_total = total_subtotal + total_iva

                # Guardar la factura actualizada
                invoice = form.save()
                invoice.subtotal, invoice.iva, invoice.total = total_subtotal, total_iva, grand_total
                invoice.save()

                for detail in details:
                    new_detail = InvoiceDetail.objects.create(
                        invoice=invoice,
                        product_id=int(detail['id']),
                        quantity=Decimal(detail['quantity']),
                        price=Decimal(detail['price']),
                        iva=Decimal(detail['iva']),
                        subtotal=Decimal(detail['sub'])
                    )
                    new_detail.product.reduce_stock(Decimal(detail['quantity']))

                messages.success(self.request, f"Éxito al Modificar la venta F#{invoice.id}")
                return JsonResponse({"msg": "Éxito al Modificar la venta Factura"}, status=200)
        else:
            messages.error(self.request, f"Error al actualizar la venta: {form.errors}")
            return JsonResponse({"msg": form.errors}, status=400)


class InvoiceDetailView(LoginRequiredMixin, TitleContextMixin, DetailView):
    model = Invoice
    template_name = 'invoice/detail_modal.html'
    context_object_name = 'invoice'

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        context = self.get_context_data(object=self.object)
        context['details'] = InvoiceDetail.objects.filter(invoice=self.object)
        html = render_to_string(self.template_name, context, request=request)
        return JsonResponse({'html': html})

class InvoiceDeleteView(LoginRequiredMixin, View):
    def post(self, request, pk, *args, **kwargs):
        try:
            with transaction.atomic():
                invoice = Invoice.objects.get(pk=pk)

                # Devolver stock de productos
                details = InvoiceDetail.objects.filter(invoice=invoice)
                for d in details:
                    d.product.stock += d.quantity
                    d.product.save()
                details.delete()

                invoice.delete()
                return JsonResponse({'msg': f'✅ Factura N°{pk} eliminada correctamente.'}, status=200)
        except Invoice.DoesNotExist:
            return JsonResponse({'msg': '⚠️ Factura no encontrada.'}, status=404)
        except Exception as ex:
            return JsonResponse({'msg': f'❌ Error al eliminar: {ex}'}, status=400)


class InvoiceAnnulView(LoginRequiredMixin, View):
    def post(self, request, pk, *args, **kwargs):
        try:
            with transaction.atomic():
                invoice = Invoice.objects.get(pk=pk)
                if not invoice.state:
                    return JsonResponse({'msg': '⚠️ La factura ya está anulada.'}, status=400)

                # Revertir stock
                details = InvoiceDetail.objects.filter(invoice=invoice)
                for d in details:
                    d.product.stock += d.quantity
                    d.product.save()

                invoice.state = False
                invoice.save(update_fields=['state'])

                return JsonResponse({'msg': f'🚫 Factura N°{pk} anulada correctamente.'}, status=200)
        except Invoice.DoesNotExist:
            return JsonResponse({'msg': '⚠️ Factura no encontrada.'}, status=404)
        except Exception as ex:
            return JsonResponse({'msg': f'❌ Error al anular: {ex}'}, status=400)

class InvoicePrintView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        try:
            invoice = Invoice.objects.get(pk=self.kwargs.get('pk'))
        except Invoice.DoesNotExist:
            return HttpResponse("Factura no encontrada.", status=404)

        context = {
            'invoice': invoice,
            'title1': "Impresión de Factura",
            'title2': "Detalle de Venta"
        }

        pdf = render_to_pdf('invoice/print.html', context)

        if pdf:
            # Para forzar la descarga del PDF con un nombre de archivo específico
            filename = f"Factura_{invoice.id}.pdf"
            pdf['Content-Disposition'] = f'attachment; filename="{filename}"'
            return pdf
        return HttpResponse("Error al generar el PDF.", status=500)
    
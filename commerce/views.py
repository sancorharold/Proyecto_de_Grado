from django.contrib.auth.mixins import LoginRequiredMixin
from core.mixins import TitleContextMixin
from core.models import Product
from core.utils import custom_serializer
from .forms import InvoiceForm
from .models import Invoice, InvoiceDetail, Purchase, PurchaseDetail
from django.db.models import Q
from django.urls import reverse_lazy
from django.views.generic import CreateView, ListView, UpdateView, DetailView, View
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from decimal import Decimal
from django.db import transaction
from django.template.loader import render_to_string
import json
from datetime import date

# Importar la función para renderizar PDF
from .utils import render_to_pdf


class InvoiceListView(LoginRequiredMixin, TitleContextMixin, ListView):
    model = Invoice
    template_name = "invoice/list.html"
    context_object_name = "invoices"
    paginate_by = 10

    title1 = "Autor | TeacherCode"
    title2 = "Listado de Ventas"

    def get_queryset(self):
        queryset = super().get_queryset()
        query = self.request.GET.get("q", "")
        if query:
            queryset = queryset.filter(
                Q(customer__last_name__icontains=query)
                | Q(customer__first_name__icontains=query)
            )
        return queryset


class InvoiceCreateView(LoginRequiredMixin, TitleContextMixin, CreateView):
    model = Invoice
    form_class = InvoiceForm
    template_name = "invoice/form.html"
    success_url = reverse_lazy("commerce:invoice_list")
    title1 = '"Ventas"'
    title2 = "Crear Nueva Venta"



    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["products"] = Product.active_products.only(
            "id", "description", "price", "stock", "iva"
        )
        context["detail_sales"] = []
        context["save_url"] = reverse_lazy("commerce:invoice_create")
        context["invoice_list_url"] = self.success_url
        return context

    def post(self, request, *args, **kwargs):
        form = self.get_form()
        if not form.is_valid():
            return JsonResponse({"msg": form.errors}, status=400)

        data = request.POST
        issue_date_str = data.get("issue_date")
        if not issue_date_str:
            return JsonResponse(
                {"msg": "⚠️ Debe seleccionar la fecha de emisión"}, status=400
            )

        try:
            with transaction.atomic():
                sale = Invoice.objects.create(
                    customer_id=int(data["customer"]),
                    user=request.user,
                    payment_method=data["payment_method"],
                    issue_date=issue_date_str,
                    subtotal=Decimal(data["subtotal"]),
                    iva=Decimal(data["iva"]),
                    total=Decimal(data["total"]),
                )

                try:
                    details = json.loads(data.get("detail", "[]"))
                except json.JSONDecodeError:
                    return JsonResponse(
                        {"msg": "Detalle de productos inválido"}, status=400
                    )

                for detail in details:
                    if not all(
                        k in detail for k in ("id", "quantify", "price", "iva", "sub")
                    ):
                        continue

                    inv_det = InvoiceDetail.objects.create(
                        invoice=sale,
                        product_id=int(detail["id"]),
                        quantity=Decimal(detail["quantify"]),
                        price=Decimal(detail["price"]),
                        iva=Decimal(detail["iva"]),
                        subtotal=Decimal(detail["sub"]),
                    )
                    inv_det.product.reduce_stock(Decimal(detail["quantify"]))

                messages.success(request, f"Éxito al registrar la venta F#{sale.pk}")
                return JsonResponse(
                    {"msg": f"Éxito al registrar la venta Factura F#{sale.pk}"},
                    status=200,
                )
        except Exception as ex:
            return JsonResponse({"msg": str(ex)}, status=400)


class InvoiceUpdateView(LoginRequiredMixin, TitleContextMixin, UpdateView):
    model = Invoice
    form_class = InvoiceForm
    template_name = "invoice/form.html"
    success_url = reverse_lazy("commerce:invoice_list")
    title1 = '"Venta"'
    title2 = "Editar Venta"

    def get_context_data(self, **kwargs):
        context = super().get_context_data()
        context["products"] = Product.active_products.only(
            "id", "description", "price", "stock", "iva"
        )
        context["invoice_list_url"] = self.success_url
        detail_sale = list(
            InvoiceDetail.objects.filter(invoice_id=self.object.id).values(
                "product",
                "product__description",
                "quantity",
                "price",
                "subtotal",
                "iva",
            )
        )
        detail_sale = json.dumps(detail_sale, default=custom_serializer)
        context["detail_sales"] = detail_sale
        context["save_url"] = reverse_lazy(
            "commerce:invoice_update", kwargs={"pk": self.object.id}
        )
        return context

    def post(self, request, *args, **kwargs):
        form = self.get_form()
        if not form.is_valid():
            return JsonResponse({"msg": form.errors}, status=400)
        data = request.POST
        try:
            sale = Invoice.objects.get(id=self.kwargs.get("pk"))

            with transaction.atomic():
                sale.customer_pk = int(data["customer"])
                sale.user = request.user
                sale.payment_method = data["payment_method"]
                sale.issue_date = data["issue_date"]
                sale.subtotal = Decimal(data["subtotal"])
                sale.iva = Decimal(data["iva"])
                sale.total = Decimal(data["total"])
                sale.save()

                details = json.loads(request.POST["detail"])
                detdelete = InvoiceDetail.objects.filter(invoice_id=sale.pk)
                for det in detdelete:
                    det.product.stock += int(det.quantity)
                    det.product.save()
                detdelete.delete()

                for detail in details:
                    inv_det = InvoiceDetail.objects.create(
                        invoice=sale,
                        product_id=int(detail["id"]),
                        quantity=Decimal(detail["quantify"]),
                        price=Decimal(detail["price"]),
                        iva=Decimal(detail["iva"]),
                        subtotal=Decimal(detail["sub"]),
                    )
                    inv_det.product.reduce_stock(Decimal(detail["quantify"]))
                messages.success(
                    self.request, f"Éxito al Modificar la venta F#{sale.pk}"
                )
                return JsonResponse(
                    {"msg": "Éxito al Modificar la venta Factura"}, status=200
                )
        except Exception as ex:
            return JsonResponse({"msg": str(ex)}, status=400)


class InvoiceDetailView(LoginRequiredMixin, TitleContextMixin, DetailView):
    model = Invoice
    template_name = "invoice/detail_modal.html"
    context_object_name = "invoice"

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        context = self.get_context_data(object=self.object)
        context["details"] = InvoiceDetail.objects.filter(invoice=self.object)
        html = render_to_string(self.template_name, context, request=request)
        return JsonResponse({"html": html})


class InvoiceDeleteView(LoginRequiredMixin, View):
    def post(self, request, pk, *args, **kwargs):
        try:
            with transaction.atomic():
                invoice = Invoice.objects.get(pk=pk)
                details = InvoiceDetail.objects.filter(invoice=invoice)
                for d in details:
                    d.product.stock += d.quantity
                    d.product.save()
                details.delete()
                invoice.delete()
                return JsonResponse(
                    {"msg": f"✅ Factura N°{pk} eliminada correctamente."}, status=200
                )
        except Invoice.DoesNotExist:
            return JsonResponse({"msg": "⚠️ Factura no encontrada."}, status=404)
        except Exception as ex:
            return JsonResponse({"msg": f"❌ Error al eliminar: {ex}"}, status=400)


class InvoiceAnnulView(LoginRequiredMixin, View):
    def post(self, request, pk, *args, **kwargs):
        try:
            with transaction.atomic():
                invoice = Invoice.objects.get(pk=pk)
                if not invoice.state:
                    return JsonResponse(
                        {"msg": "⚠️ La factura ya está anulada."}, status=400
                    )

                details = InvoiceDetail.objects.filter(invoice=invoice)
                for d in details:
                    d.product.stock += d.quantity
                    d.product.save()

                invoice.state = False
                invoice.save(update_fields=["state"])

                return JsonResponse(
                    {"msg": f"🚫 Factura N°{pk} anulada correctamente."}, status=200
                )
        except Invoice.DoesNotExist:
            return JsonResponse({"msg": "⚠️ Factura no encontrada."}, status=404)
        except Exception as ex:
            return JsonResponse({"msg": f"❌ Error al anular: {ex}"}, status=400)


# VISTA PARA GENERAR PDF DE LA FACTURA
class InvoicePrintView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        try:
            invoice = Invoice.objects.get(pk=self.kwargs.get("pk"))
        except Invoice.DoesNotExist:
            return HttpResponse("Factura no encontrada.", status=404)

        context = {
            "invoice": invoice,
            "title1": "Impresión de Factura",
            "title2": "Detalle de Venta",
        }

        pdf = render_to_pdf("invoice/print.html", context)

        if pdf:
            filename = f"Factura_{invoice.pk}.pdf"
            pdf["Content-Disposition"] = f'attachment; filename="{filename}"'
            return pdf
        return HttpResponse("Error al generar el PDF.", status=500)



from django.contrib.auth.mixins import LoginRequiredMixin
from core.mixins import TitleContextMixin
from core.models import Product
from core.utils import custom_serializer
from .forms import InvoiceForm
from .models import Invoice, InvoiceDetail
from django.db.models import Q
from django.urls import reverse_lazy
from django.views.generic import CreateView, ListView, UpdateView, DetailView, View
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from decimal import Decimal
from django.db import transaction
from django.template.loader import render_to_string
import json
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import transaction
from django.http import JsonResponse
from django.urls import reverse_lazy
from django.db.models import Q
from django.views.generic import (
    ListView,
    CreateView,
    UpdateView,
    DeleteView,
    View,
    DetailView,
)

from core.mixins import TitleContextMixin
from .models import Invoice, InvoiceDetail
from core.models import Product
from .forms import InvoiceForm
from .utils import render_to_pdf


class InvoiceListView(LoginRequiredMixin, TitleContextMixin, ListView):
    model = Invoice
    template_name = "invoice/list.html"
    context_object_name = "invoices"
    paginate_by = 10
    title2 = "Listado de Facturas"

    def get_queryset(self):
        queryset = super().get_queryset()
        query = self.request.GET.get("q", "")
        if query:
            queryset = queryset.filter(
                Q(customer__first_name__icontains=query)
                | Q(customer__last_name__icontains=query)
            )
        return queryset


class InvoiceCreateView(LoginRequiredMixin, TitleContextMixin, CreateView):
    model = Invoice
    form_class = InvoiceForm
    template_name = "invoice/form.html"
    success_url = reverse_lazy("commerce:invoice_list")
    title2 = "Nueva Factura"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["products"] = Product.active_products.all()
        return context

    def form_valid(self, form):
        try:
            with transaction.atomic():
                invoice = form.save(commit=False)
                invoice.user = self.request.user
                invoice.save()

                detail_data = json.loads(self.request.POST.get("detail", "[]"))
                for item in detail_data:
                    product = Product.objects.get(pk=item["id"])
                    InvoiceDetail.objects.create(
                        invoice=invoice,
                        product=product,
                        quantity=item["quantify"],
                        price=item["price"],
                        cost=product.cost,
                        subtotal=item["sub"],
                        iva=item["iva"],
                    )
                    product.reduce_stock(item["quantify"])

                return JsonResponse(
                    {"msg": "Factura guardada con éxito.", "url": self.success_url}
                )
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=400)


from django.http import JsonResponse

class InvoiceUpdateView(LoginRequiredMixin, TitleContextMixin, UpdateView):
    model = Invoice
    form_class = InvoiceForm
    template_name = "invoice/form.html"
    success_url = reverse_lazy("commerce:invoice_list")
    title2 = "Editar Factura"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["products"] = Product.active_products.all()
        details = InvoiceDetail.objects.filter(invoice=self.object)
        context["detail_sales"] = json.dumps(
            [
                {
                    "product": d.product.id,
                    "product__description": d.product.description,
                    "quantity": float(d.quantity),
                    "price": float(d.price),
                    "subtotal": float(d.subtotal),
                    "iva": float(d.iva),
                }
                for d in details
            ]
        )
        return context

    def form_valid(self, form):
        self.object = form.save()
        # Aquí podrías procesar el detalle enviado desde JS
        import json
        detail_data = json.loads(self.request.POST.get("detail", "[]"))
        # Guardar detalle_data en InvoiceDetail...
        # Luego devolver JSON
        return JsonResponse({"msg": "Factura actualizada con éxito"})

    def form_invalid(self, form):
        return JsonResponse({"error": form.errors}, status=400)


class InvoiceDeleteView(LoginRequiredMixin, View):
    def post(self, request, pk, *args, **kwargs):
        try:
            invoice = Invoice.objects.get(pk=pk)
            invoice.delete()
            return JsonResponse({"msg": "Factura eliminada correctamente."})
        except Invoice.DoesNotExist:
            return JsonResponse({"error": "Factura no encontrada."}, status=404)


class InvoiceAnnulView(LoginRequiredMixin, View):
    def post(self, request, pk, *args, **kwargs):
        invoice = Invoice.objects.get(pk=pk)
        invoice.state = False
        invoice.save()
        return JsonResponse({"msg": "Factura anulada correctamente."})


class InvoiceDetailView(LoginRequiredMixin, DetailView):
    model = Invoice
    template_name = "invoice/detail_modal.html"

    def get(self, request, *args, **kwargs):
        from django.template.loader import render_to_string

        invoice = self.get_object()
        html = render_to_string(self.template_name, {"invoice": invoice})
        return JsonResponse({"html": html})


class InvoicePrintView(LoginRequiredMixin, View):
    def get(self, request, pk, *args, **kwargs):
        invoice = Invoice.objects.get(pk=pk)
        pdf = render_to_pdf("invoice/print.html", {"invoice": invoice})
        return pdf

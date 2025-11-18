from django.contrib.auth.mixins import LoginRequiredMixin
from core.mixins import TitleContextMixin
from django.views.generic import ListView, CreateView, UpdateView, DetailView, View
from django.urls import reverse_lazy
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.db import transaction
from django.db.models import Q
from django.template.loader import render_to_string
from decimal import Decimal
import json

from core.models import Product, Supplier
from .models import Purchase, PurchaseDetail
from .forms import PurchaseForm
from .utils import render_to_pdf
from commerce.commerce_mixins import QueryFilterMixin


# ===================== LISTADO =====================
class PurchaseListView(LoginRequiredMixin, TitleContextMixin, QueryFilterMixin, ListView):
    model = Purchase
    template_name = "purchase/list.html"
    context_object_name = "purchases"
    paginate_by = 10
    title2 = "Listado de Compras"
    search_fields = ["supplier__name", "num_document"]



# ===================== CREAR COMPRA =====================
class PurchaseCreateView(LoginRequiredMixin, TitleContextMixin, CreateView):
    model = Purchase
    form_class = PurchaseForm
    template_name = "purchase/form.html"
    success_url = reverse_lazy("purchase:purchase_list")
    title2 = "Registrar Nueva Compra"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["products"] = Product.active_products.all()
        return context

    def form_valid(self, form):
        try:
            with transaction.atomic():
                purchase = form.save(commit=False)
                purchase.user = self.request.user
                purchase.save()

                detail_data = json.loads(self.request.POST.get("detail", "[]"))

                for item in detail_data:
                    product = Product.objects.get(pk=item["id"])

                    PurchaseDetail.objects.create(
                        purchase=purchase,
                        product=product,
                        quantity=item["quantify"],
                        cost=item["price"],
                        subtotal=item["sub"],
                        iva=item["iva"]
                    )

                    # Aumentar stock
                    product.stock += Decimal(item["quantify"])
                    product.save()

                return JsonResponse({"msg": "Compra registrada con éxito.", "url": self.success_url})

        except Exception as e:
            return JsonResponse({"error": str(e)}, status=400)


# ===================== EDITAR COMPRA =====================
class PurchaseUpdateView(LoginRequiredMixin, TitleContextMixin, UpdateView):
    model = Purchase
    form_class = PurchaseForm
    template_name = "purchase/form.html"
    success_url = reverse_lazy("purchase:purchase_list")
    title2 = "Editar Compra"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["products"] = Product.active_products.all()

        details = PurchaseDetail.objects.filter(purchase=self.object)

        context["detail_purchase"] = json.dumps([
            {
                "product": d.product.id,
                "product__description": d.product.description,
                "quantity": float(d.quantity),
                "price": float(d.cost),
                "subtotal": float(d.subtotal),
                "iva": float(d.iva),
            }
            for d in details
        ])

        return context

    def form_valid(self, form):
        try:
            with transaction.atomic():
                purchase = form.save()

                # Devolver stock anterior
                old_details = PurchaseDetail.objects.filter(purchase=purchase)
                for d in old_details:
                    d.product.stock -= d.quantity
                    d.product.save()
                old_details.delete()

                # Agregar nuevos detalles
                detail_data = json.loads(self.request.POST.get("detail", "[]"))
                for item in detail_data:
                    product = Product.objects.get(pk=item["id"])

                    PurchaseDetail.objects.create(
                        purchase=purchase,
                        product=product,
                        quantity=item["quantify"],
                        cost=item["price"],
                        subtotal=item["sub"],
                        iva=item["iva"],
                    )

                    product.stock += Decimal(item["quantify"])
                    product.save()

                return JsonResponse({"msg": "Compra actualizada con éxito.", "url": self.success_url})
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=400)


# ===================== ELIMINAR COMPRA =====================
class PurchaseDeleteView(LoginRequiredMixin, View):
    def post(self, request, pk, *args, **kwargs):
        try:
            purchase = Purchase.objects.get(pk=pk)

            details = PurchaseDetail.objects.filter(purchase=purchase)
            for d in details:
                d.product.stock -= d.quantity
                d.product.save()

            details.delete()
            purchase.delete()

            return JsonResponse({"msg": "Compra eliminada correctamente."})

        except Purchase.DoesNotExist:
            return JsonResponse({"error": "Compra no encontrada."}, status=404)


# ===================== ANULAR COMPRA =====================
class PurchaseAnnulView(LoginRequiredMixin, View):
    def post(self, request, pk, *args, **kwargs):
        try:
            purchase = Purchase.objects.get(pk=pk)

            if not purchase.state:
                return JsonResponse({"msg": "La compra ya está anulada."}, status=400)

            purchase.state = False
            purchase.save()

            # Revertir stock
            details = PurchaseDetail.objects.filter(purchase=purchase)
            for d in details:
                d.product.stock -= d.quantity
                d.product.save()

            return JsonResponse({"msg": "Compra anulada correctamente."})
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=400)


# ===================== DETALLE =====================
class PurchaseDetailView(LoginRequiredMixin, DetailView):
    model = Purchase
    template_name = "purchase/detail_modal.html"

    def get(self, request, *args, **kwargs):
        purchase = self.get_object()
        details = PurchaseDetail.objects.filter(purchase=purchase)

        html = render_to_string(self.template_name, {
            "purchase": purchase,
            "details": details
        })

        return JsonResponse({"html": html})


# ===================== IMPRIMIR =====================
class PurchasePrintView(LoginRequiredMixin, View):
    def get(self, request, pk, *args, **kwargs):
        purchase = Purchase.objects.get(pk=pk)
        pdf = render_to_pdf("purchase/print.html", {"purchase": purchase})
        return pdf

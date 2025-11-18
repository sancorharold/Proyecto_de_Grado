import json
from django.contrib.auth.mixins import LoginRequiredMixin
from core.utils import custom_serializer
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


# ===================== LISTADO =====================
class PurchaseListView(LoginRequiredMixin, TitleContextMixin, ListView):
    model = Purchase
    template_name = "purchase/list.html"
    context_object_name = "purchases"
    paginate_by = 10
    title2 = "Listado de Compras"

    def get_queryset(self):
        queryset = super().get_queryset()
        query = self.request.GET.get("q", "")
        if query:
            queryset = queryset.filter(
                Q(supplier__name__icontains=query) |
                Q(num_document__icontains=query)
            )
        return queryset


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
        # Pasamos las URLs y un array vacío para los detalles, ya que es una creación
        context["save_url"] = self.success_url
        context["detail_purchase"] = "[]" 
        # Aseguramos que el nombre de la variable sea consistente con la de edición
        context["purchase_list_url"] = reverse_lazy("purchase:purchase_list")
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
                        quantity=item["quantity"],
                        cost=item["cost"],
                        subtotal=item["subtotal"],
                        iva=Decimal(item["subtotal"]) - (Decimal(item["cost"]) * Decimal(item["quantity"])),
                    )
                    # Actualizar stock y costo del producto
                    product.stock += Decimal(item["quantity"])
                    product.cost = Decimal(item["cost"])
                    product.save()
                return JsonResponse({"msg": "Compra guardada con éxito.", "url": self.success_url})
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
                "quantity": d.quantity,
                "cost": d.cost,
                "subtotal": d.subtotal,
                "product__iva": d.product.iva,
            }
            for d in details], default=custom_serializer)
        
        context["save_url"] = self.object.get_absolute_url() if hasattr(self.object, 'get_absolute_url') else reverse_lazy('purchase:purchase_update', kwargs={'pk': self.object.pk})
        context["purchase_list_url"] = self.success_url
        return context

    def form_valid(self, form):
        try:
            with transaction.atomic():
                purchase = form.save()
                
                # Revertir stock de detalles antiguos antes de borrarlos
                for d in purchase.detail.all():
                    d.product.stock -= d.quantity
                    d.product.save()
                purchase.detail.all().delete()

                # Guardar los nuevos detalles y actualizar stock
                detail_data = json.loads(self.request.POST.get("detail", "[]"))
                for item in detail_data:
                    product = Product.objects.get(pk=item["id"])
                    PurchaseDetail.objects.create(
                        purchase=purchase,
                        product=product,
                        quantity=item["quantity"],
                        cost=item["cost"],
                        subtotal=item["subtotal"],
                        iva=item["subtotal"] - (Decimal(item["cost"]) * Decimal(item["quantity"])),
                    )
                    product.stock += Decimal(item["quantity"])
                    product.cost = Decimal(item["cost"])
                    product.save()

                return JsonResponse({"msg": "Compra actualizada con éxito.", "url": self.success_url})
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=400)


# ===================== ELIMINAR COMPRA =====================
class PurchaseDeleteView(LoginRequiredMixin, TitleContextMixin, View):
    def post(self, request, pk, *args, **kwargs):
        # Usamos post para que la eliminación no se pueda hacer con un simple GET
        try:
            with transaction.atomic():
                purchase = Purchase.objects.get(pk=pk)

                # Revertir el stock de cada producto en el detalle
                for detail in purchase.detail.all():
                    product = detail.product
                    product.stock -= detail.quantity
                    product.save()

                # Eliminar la compra (y sus detalles en cascada si se configura)
                purchase.delete()

                # Usar messages para notificar en la siguiente página
                messages.success(request, f"Compra N° {pk} eliminada y stock revertido.")

            return JsonResponse({"msg": "Compra eliminada correctamente."})

        except Purchase.DoesNotExist:
            return JsonResponse({"error": "Compra no encontrada."}, status=404)


# ===================== ANULAR COMPRA =====================
class PurchaseAnnulView(LoginRequiredMixin, TitleContextMixin, View):
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
class PurchaseDetailView(LoginRequiredMixin, TitleContextMixin, DetailView):
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
class PurchasePrintView(LoginRequiredMixin, TitleContextMixin, View):
    def get(self, request, pk, *args, **kwargs):
        purchase = Purchase.objects.get(pk=pk)
        pdf = render_to_pdf("purchase/print.html", {"purchase": purchase})
        return pdf

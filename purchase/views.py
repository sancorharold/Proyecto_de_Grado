import json
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.db.models import Q
from django.db import transaction
from django.http import JsonResponse

from core.mixins import TitleContextMixin
from .models import Purchase, PurchaseDetail
from .forms import PurchaseForm
from core.models import Product


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
                Q(supplier__name__icontains=query) | Q(num_document__icontains=query)
            )
        return queryset


class PurchaseCreateView(LoginRequiredMixin, TitleContextMixin, CreateView):
    model = Purchase
    form_class = PurchaseForm
    template_name = "purchase/form.html"
    success_url = reverse_lazy("purchase:purchase_list")
    title2 = "Registrar Nueva Compra"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["products"] = Product.objects.filter(state=True)
        return context

    def form_valid(self, form):
        try:
            with transaction.atomic():
                # Guardar la cabecera de la compra
                purchase = form.save(commit=False)
                purchase.user = self.request.user
                purchase.save()

                # Guardar los detalles
                detail_data = json.loads(self.request.POST.get("detail", "[]"))
                for item in detail_data:
                    product = Product.objects.get(pk=item["id"])
                    PurchaseDetail.objects.create(
                        purchase=purchase,
                        product=product,
                        quantity=item["quantity"],
                        cost=item["cost"],
                        subtotal=item["subtotal"],
                        iva=item["subtotal"] - (item["cost"] * item["quantity"]),
                    )
                    # Actualizar stock y costo del producto
                    product.stock += item["quantity"]
                    product.cost = item["cost"]
                    product.save()
                return JsonResponse({"msg": "Compra guardada con éxito.", "url": self.success_url})
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=400)

class PurchaseUpdateView(LoginRequiredMixin, TitleContextMixin, UpdateView):
    model = Purchase
    form_class = PurchaseForm
    template_name = "purchase/form.html"
    success_url = reverse_lazy("purchase:purchase_list")
    title2 = "Editar Compra"
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["products"] = Product.objects.filter(state=True)
        details = PurchaseDetail.objects.filter(purchase=self.object)
        # Preparamos los detalles para pasarlos como JSON al template
        context["detail_purchases"] = json.dumps([
            {"product": d.product.id, "product__description": d.product.description, 
             "quantity": d.quantity, "cost": d.cost, "subtotal": d.subtotal,
             "product__iva": d.product.iva}
            for d in details
        ])
        return context

    def form_valid(self, form):
        try:
            with transaction.atomic():
                # Guardar la cabecera de la compra
                purchase = form.save()

                # Limpiar detalles antiguos para reemplazarlos
                purchase.detail.all().delete()

                # Guardar los nuevos detalles
                detail_data = json.loads(self.request.POST.get("detail", "[]"))
                for item in detail_data:
                    product = Product.objects.get(pk=item["id"])
                    PurchaseDetail.objects.create(
                        purchase=purchase,
                        product=product,
                        quantity=item["quantity"],
                        cost=item["cost"],
                        subtotal=item["subtotal"],
                        iva=item["subtotal"] - (item["cost"] * item["quantity"]),
                    )
                    # Nota: La lógica de actualización de stock al editar es compleja.
                    # Por ahora, la omitimos para evitar inconsistencias.
                
                return JsonResponse({"msg": "Compra actualizada con éxito.", "url": self.success_url})
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=400)


class PurchaseDeleteView(LoginRequiredMixin, TitleContextMixin, DeleteView):
    model = Purchase
    template_name = "purchase/delete.html"
    success_url = reverse_lazy("purchase:purchase_list")
    title2 = "Eliminar Compra"

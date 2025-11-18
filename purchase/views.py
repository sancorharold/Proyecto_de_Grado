from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.db.models import Q

from core.mixins import TitleContextMixin
from .models import Purchase
from .forms import PurchaseForm


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

    def form_valid(self, form):
        form.instance.user = self.request.user
        # Aquí iría la lógica para guardar los detalles de la compra
        return super().form_valid(form)


class PurchaseUpdateView(LoginRequiredMixin, TitleContextMixin, UpdateView):
    model = Purchase
    form_class = PurchaseForm
    template_name = "purchase/form.html"
    success_url = reverse_lazy("purchase:purchase_list")
    title2 = "Editar Compra"


class PurchaseDeleteView(LoginRequiredMixin, TitleContextMixin, DeleteView):
    model = Purchase
    template_name = "purchase/delete.html"
    success_url = reverse_lazy("purchase:purchase_list")
    title2 = "Eliminar Compra"

from django.shortcuts import render
from django.views.generic import (
    ListView,
    CreateView,
    UpdateView,
    DeleteView,
    TemplateView,
)
from django.contrib.auth.mixins import LoginRequiredMixin
from core.mixins import TitleContextMixin
from core.forms import SupplierForm, BrandForm
from .models import Customer, Supplier, Brand
from django.contrib import messages
from django.shortcuts import redirect
from django.db import models
from django.db.models import Q
from django.urls import reverse_lazy
from django.http import JsonResponse
from django.views.generic import (
    CreateView,
    ListView,
    UpdateView,
    DeleteView,
    DetailView,
)
from django.views import View


def home(request):
    data = {"title1": "Autor | TeacherCode", "title2": "Super Mercado Economico"}

    return render(request, "home.html", data)


class HomeTemplateView(TitleContextMixin, TemplateView):

    template_name = "home.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["suppliers"] = Supplier.objects.count()
        return context


class SupplierListView(LoginRequiredMixin, TitleContextMixin, ListView):
    model = Supplier
    template_name = "supplier/list.html"  # Nombre del template a usar
    context_object_name = "suppliers"  # Nombre del contexto a pasar al template
    paginate_by = 10
    title1 = None
    title2 = None
    title1 = "Autor | TeacherCode"
    title2 = "Listado de Proveedores mixings"

    def get_queryset(self):
        # Se Puede personalizar el queryset aquí si es necesario
        queryset = super().get_queryset()  # self.model.objects.all()
        query = self.request.GET.get("q", "")
        if query:
            queryset = queryset.filter(
                Q(name__icontains=query) | Q(ruc__icontains=query)
            )
        return queryset


class SupplierCreateView(LoginRequiredMixin, TitleContextMixin, CreateView):
    model = Supplier
    form_class = SupplierForm
    template_name = "supplier/form.html"
    success_url = reverse_lazy(
        "core:supplier_list"
    )  # Redirigir a la lista de proveedores después de crear uno nuevo
    title1 = '"Proveedores"'
    title2 = "Crear Nuevo Proveedor VBC"

    def form_valid(self, form):
        form.instance.user = self.request.user
        return super().form_valid(form)


class BrandListView(LoginRequiredMixin, TitleContextMixin, ListView):
    model = Brand
    template_name = "brand/list.html"
    context_object_name = "brands"
    title2 = "Listado de Marcas"


class BrandCreateView(LoginRequiredMixin, TitleContextMixin, CreateView):
    model = Brand
    form_class = BrandForm
    template_name = "brand/form.html"  # Deberás crear esta plantilla
    success_url = reverse_lazy("core:brand_list")  # Deberás crear esta URL
    title1 = "Marcas"
    title2 = "Crear Nueva Marca"


class BrandUpdateView(LoginRequiredMixin, TitleContextMixin, UpdateView):
    model = Brand
    form_class = BrandForm
    template_name = "brand/form.html"
    success_url = reverse_lazy("core:brand_list")
    title1 = "Marcas"
    title2 = "Editar Marca"


class BrandDeleteView(LoginRequiredMixin, TitleContextMixin, DeleteView):
    model = Brand
    template_name = "brand/delete.html"
    success_url = reverse_lazy("core:brand_list")
    title1 = "Marcas"
    title2 = "Eliminar Marca"

    def post(self, request, *args, **kwargs):
        try:
            return super().post(request, *args, **kwargs)
        except models.ProtectedError:
            messages.error(
                request,
                "No se puede eliminar esta marca porque tiene productos asociados.",
            )
            return redirect("core:brand_list")


class SupplierUpdateView(LoginRequiredMixin, TitleContextMixin, UpdateView):
    model = Supplier
    form_class = SupplierForm
    template_name = "supplier/form.html"
    success_url = reverse_lazy(
        "core:supplier_list"
    )  # Redirigir a la lista de proveedores después de crear uno nuevo
    title1 = '"Proveedores"'
    title2 = "Editar Proveedor"


class SupplierDetailView(LoginRequiredMixin, TitleContextMixin, DetailView):
    model = Supplier
    template_name = "supplier/detail.html"
    context_object_name = "supplier"  # nombre del objeto en el template
    title1 = "Proveedores"
    title2 = "Datos del Proveedor"
    success_url = reverse_lazy("core:supplier_list")


class SupplierDeleteView(LoginRequiredMixin, TitleContextMixin, DeleteView):
    model = Supplier
    template_name = "supplier/delete.html"
    success_url = reverse_lazy("core:supplier_list")
    title1 = "Eliminar"
    title2 = "Eliminar Proveedor VBC"


class CustomerSearchView(LoginRequiredMixin, View):
    def get(self, request):
        query = request.GET.get("term", "")
        customers = Customer.objects.filter(
            Q(first_name__icontains=query)
            | Q(last_name__icontains=query)
            | Q(dni__icontains=query)
        ).filter(state=True)[
            :10
        ]  # Limita a 10 resultados

        results = []
        for customer in customers:
            results.append({"id": customer.pk, "text": customer.get_full_name})

        return JsonResponse({"results": results})

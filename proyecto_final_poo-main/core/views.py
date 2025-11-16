from django.shortcuts import render
from django.views.generic import ListView,CreateView,UpdateView,DeleteView, TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from core.mixins import TitleContextMixin
from core.forms import SupplierForm
from .models import Customer, Supplier 
from django.shortcuts import redirect, render
from django.db.models import Q
from django.urls import reverse_lazy
from django.views.generic import CreateView, ListView, UpdateView, DeleteView,DetailView


def home(request):
    data = {
        "title1":"Autor | TeacherCode",
        "title2":"Super Mercado Economico"
    }
   
    return render(request,'home.html',data)

class HomeTemplateView(TitleContextMixin,TemplateView):
   
    template_name = 'home.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["suppliers"] = Supplier.objects.count()
        return context

class SupplierListView(LoginRequiredMixin,TitleContextMixin,ListView): 
    model = Supplier 
    template_name = 'supplier/list.html'  # Nombre del template a usar 
    context_object_name = 'suppliers'     # Nombre del contexto a pasar al template 
    paginate_by = 10   
    title1 = None
    title2 = None                 
    title1 = "Autor | TeacherCode"
    title2 = "Listado de Proveedores mixings"

    def get_queryset(self):
        # Se Puede personalizar el queryset aquí si es necesario
        queryset = super().get_queryset()  # self.model.objects.all()
        query = self.request.GET.get('q','')
        if query:
            queryset = queryset.filter(Q(name__icontains=query) | Q(ruc__icontains=query))
        return queryset
    
   
class SupplierCreateView(LoginRequiredMixin,TitleContextMixin,CreateView):
    model = Supplier
    form_class = SupplierForm
    template_name = "supplier/form.html"
    success_url = reverse_lazy("core:supplier_list")  # Redirigir a la lista de proveedores después de crear uno nuevo
    title1 = '"Proveedores"'
    title2 = 'Crear Nuevo Proveedor VBC'
          
    def form_valid(self, form):
        form.instance.user = self.request.user
        return super().form_valid(form)

class SupplierUpdateView(LoginRequiredMixin,TitleContextMixin,UpdateView):
    model = Supplier
    form_class = SupplierForm
    template_name = "supplier/form.html"
    success_url = reverse_lazy("core:supplier_list")  # Redirigir a la lista de proveedores después de crear uno nuevo
    title1 = '"Proveedores"'
    title2 = 'Editar Proveedor'
   
    def form_valid(self, form):
        form.instance.user = self.request.user
        return super().form_valid(form)


class SupplierDetailView(LoginRequiredMixin, TitleContextMixin, DetailView):
    model = Supplier
    template_name = "supplier/detail.html"
    context_object_name = "supplier"  # nombre del objeto en el template
    title1 = "Proveedores"
    title2 = "Datos del Proveedor"
    success_url = reverse_lazy("core:supplier_list")

class SupplierDeleteView(LoginRequiredMixin,TitleContextMixin,DeleteView):
    model = Supplier
    template_name = "supplier/delete.html"
    success_url = reverse_lazy("core:supplier_list") 
    title1 = "Eliminar"
    title2 = 'Eliminar Proveedor VBC'
   


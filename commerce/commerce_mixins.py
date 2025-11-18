from django.db.models import Q


class QueryFilterMixin:
    """
    Mixin genérico para filtrar queryset basado en un parámetro GET `q`.
    Definir `search_fields` como lista de campos para buscar.
    Ejemplo:
        search_fields = ['customer__first_name', 'customer__last_name']
    """

    search_param = "q"  # Nombre del parámetro GET
    search_fields = []   # Campos sobre los que buscar

    def get_queryset(self):
        queryset = super().get_queryset()
        query = self.request.GET.get(self.search_param, "")
        if query and self.search_fields:
            # Construir Q dinámicamente
            q_object = Q()
            for field in self.search_fields:
                q_object |= Q(**{f"{field}__icontains": query})
            queryset = queryset.filter(q_object)
        return queryset
from django.contrib import admin

from core.models import *

@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
    list_display = ('name', 'ruc', 'user', 'created', 'state')
    readonly_fields = ('user', 'created', 'updated')
    search_fields = ('name', 'ruc')
    list_filter = ('state',)

    def save_model(self, request, obj, form, change):
        # Si el objeto es nuevo (no está siendo editado), asigna el usuario actual.
        if not change:
            obj.user = request.user
        super().save_model(request, obj, form, change)

admin.site.register(Customer)
admin.site.register(Brand)
admin.site.register(Category)
admin.site.register(Product)

from django.urls import path
from commerce import views

app_name = "commerce"  # define un espacio de nombre para la aplicacion
urlpatterns = [
    path("invoice_list/", views.InvoiceListView.as_view(), name="invoice_list"),
    path("invoice_create/", views.InvoiceCreateView.as_view(), name="invoice_create"),
    path(
        "invoice_update/<int:pk>/",
        views.InvoiceUpdateView.as_view(),
        name="invoice_update",
    ),
    path(
        "invoice_detail/<int:pk>/",
        views.InvoiceDetailView.as_view(),
        name="invoice_detail",
    ),
    path(
        "invoice_annul/<int:pk>/",
        views.InvoiceAnnulView.as_view(),
        name="invoice_annul",
    ),
    path(
        "invoice_delete/<int:pk>/",
        views.InvoiceDeleteView.as_view(),
        name="invoice_delete",
    ),
    path(
        "invoice_print/<int:pk>/",
        views.InvoicePrintView.as_view(),
        name="invoice_print",
    ),  # Imprimir factura
]

from django.urls import path
from . import views

app_name = "commerce"


urlpatterns = [
    # URLs para Facturas (Invoices)
    path("invoice/list/", views.InvoiceListView.as_view(), name="invoice_list"),
    path("invoice/create/", views.InvoiceCreateView.as_view(), name="invoice_create"),
    path(
        "invoice/update/<int:pk>/",
        views.InvoiceUpdateView.as_view(),
        name="invoice_update",
    ),
    path(
        "invoice/delete/<int:pk>/",
        views.InvoiceDeleteView.as_view(),
        name="invoice_delete",
    ),
    path(
        "invoice/annul/<int:pk>/",
        views.InvoiceAnnulView.as_view(),
        name="invoice_annul",
    ),
    path(
        "invoice/detail/<int:pk>/",
        views.InvoiceDetailView.as_view(),
        name="invoice_detail",
    ),
    path(
        "invoice/print/<int:pk>/",
        views.InvoicePrintView.as_view(),
        name="invoice_print",
    ),
]

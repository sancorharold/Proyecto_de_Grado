from django.urls import path
from . import views

app_name = "purchase"

urlpatterns = [
    path("list/", views.PurchaseListView.as_view(), name="purchase_list"),
    path("create/", views.PurchaseCreateView.as_view(), name="purchase_create"),
    path(
        "update/<int:pk>/", views.PurchaseUpdateView.as_view(), name="purchase_update"
    ),
    path(
        "delete/<int:pk>/", views.PurchaseDeleteView.as_view(), name="purchase_delete"
    ),
    path("print/<int:pk>/", views.PurchasePrintView.as_view(), name="purchase_print"),
]

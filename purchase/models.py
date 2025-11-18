from django.db import models
from core.models import Product, Supplier
from django.utils import timezone
from django.contrib.auth.models import User


class Purchase(models.Model):
    num_document = models.CharField(
        verbose_name="NumDocumento", max_length=50, blank=True, null=True
    )
    supplier = models.ForeignKey(
        Supplier,
        on_delete=models.PROTECT,
        related_name="purchase_suppliers",
        verbose_name="Proveedor",
    )
    issue_date = models.DateTimeField(
        verbose_name="Fecha Emision", default=timezone.now, db_index=True
    )
    subtotal = models.DecimalField(
        verbose_name="Subtotal", default=0, max_digits=16, decimal_places=2
    )
    iva = models.DecimalField(
        verbose_name="Iva", default=0, max_digits=16, decimal_places=2
    )
    total = models.DecimalField(
        verbose_name="Total", default=0, max_digits=16, decimal_places=2
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    state = models.BooleanField(verbose_name="Activo", default=True)

    class Meta:
        verbose_name = "Compra de Producto"
        verbose_name_plural = "Compras de Productos"
        ordering = ("-issue_date",)

    def __str__(self):
        return f"{self.num_document or 'S/N'} - {self.issue_date:%d-%m-%Y}"


class PurchaseDetail(models.Model):
    purchase = models.ForeignKey(
        Purchase,
        on_delete=models.PROTECT,
        related_name="detail",
        verbose_name="Compra",
    )
    product = models.ForeignKey(
        Product, on_delete=models.PROTECT, related_name="purchase_products"
    )
    quantity = models.DecimalField(
        verbose_name="Cantidad", default=0, max_digits=8, decimal_places=2
    )
    cost = models.DecimalField(
        verbose_name="Costo", default=0, max_digits=16, decimal_places=2
    )
    subtotal = models.DecimalField(
        verbose_name="Subtotal", default=0, max_digits=16, decimal_places=2
    )
    iva = models.DecimalField(
        verbose_name="Iva", default=0, max_digits=16, decimal_places=2
    )

    class Meta:
        verbose_name = "Detalle de Compra"
        verbose_name_plural = "Detalles de la Compra"
        ordering = ("id",)

    def __str__(self):
        return f"{self.purchase} - {self.product.description}"
from django.db import models
from decimal import Decimal
from dateutil.relativedelta import relativedelta

# Create your models here.
class TipoPrestamo(models.Model):
    descripcion = models.CharField(max_length=100)
    tasa = models.IntegerField(default=0)  # Porcentaje anual o mensual

    def __str__(self):
        return self.descripcion

class Empleado(models.Model):
    nombres = models.CharField(max_length=100)
    sueldo = models.DecimalField(max_digits=10, decimal_places=2)
    # Otros campos relevantes del empleado
    def __str__(self):
        return self.nombres

class Prestamo(models.Model):
    empleado = models.ForeignKey(Empleado, on_delete=models.CASCADE)
    tipo_prestamo = models.ForeignKey(TipoPrestamo, on_delete=models.CASCADE)

    fecha_prestamo = models.DateField()

    monto = models.DecimalField(max_digits=10, decimal_places=2)
    interes = models.DecimalField(max_digits=10, decimal_places=2, editable=False)
    monto_pagar = models.DecimalField(max_digits=10, decimal_places=2, editable=False)
    numero_cuotas = models.PositiveIntegerField(default=1)

    saldo = models.DecimalField(max_digits=10, decimal_places=2, editable=False)

    ESTADOS = [
        ('PEND', 'Pendiente'),
        ('PAG', 'Pagado'),
        ('ANU', 'Anulado'),
    ]
    estado = models.CharField(max_length=4, choices=ESTADOS, default='PEND')


    def __str__(self):
        return f"Préstamo #{self.id} - {self.empleado}"

    def save(self, *args, **kwargs):
        # --- 1. Calcular los valores principales del préstamo ---
        # La tasa de interés se divide por 100 para obtener el valor decimal
        tasa_decimal = Decimal(self.tipo_prestamo.tasa) / Decimal(100)
        self.interes = self.monto * tasa_decimal
        self.monto_pagar = self.monto + self.interes
        
        # Al crear, el saldo inicial es el monto total a pagar
        if not self.pk:
            self.saldo = self.monto_pagar

        # Guardar el préstamo para obtener un ID antes de crear los detalles
        super().save(*args, **kwargs)

        # --- 2. Generar las cuotas (solo si es un préstamo nuevo) ---
        # Verificamos si ya tiene detalles para no duplicarlos en cada guardado
        if not self.detalles.exists() and self.numero_cuotas > 0:
            valor_cuota = self.monto_pagar / self.numero_cuotas

            for i in range(1, self.numero_cuotas + 1):
                # La fecha de vencimiento es un mes después de la anterior,
                # comenzando desde la fecha del préstamo.
                fecha_vencimiento = self.fecha_prestamo + relativedelta(months=i)
                
                PrestamoDetalle.objects.create(
                    prestamo=self,
                    numero_cuota=i,
                    fecha_vencimiento=fecha_vencimiento,
                    valor_cuota=valor_cuota,
                    saldo_cuota=valor_cuota  # El saldo inicial de la cuota es su valor total
                )




class PrestamoDetalle(models.Model):
    prestamo = models.ForeignKey(Prestamo, related_name='detalles', on_delete=models.CASCADE)

    numero_cuota = models.PositiveIntegerField()
    fecha_vencimiento = models.DateField()

    valor_cuota = models.DecimalField(max_digits=10, decimal_places=2)
    saldo_cuota = models.DecimalField(max_digits=10, decimal_places=2)


    def __str__(self):
        return f"Cuota {self.numero_cuota} - Prestamo {self.prestamo.id}"
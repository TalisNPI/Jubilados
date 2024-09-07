from django.db import models
from django.conf import settings

class Purchase(models.Model):
    CATEGORIES = [
        ('beverages', 'Bebidas'),
        ('food', 'Alimentos'),
        ('supplies', 'Suministros'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    item_name = models.CharField(max_length=100)
    quantity = models.PositiveIntegerField(default=1)
    category = models.CharField(max_length=10, choices=CATEGORIES)
    date = models.DateField(auto_now_add=True)

    def __str__(self):
        return f"{self.item_name} - {self.quantity} ({self.get_category_display()})"

class Articulo(models.Model):
    nombre = models.CharField(max_length=100)
    proveedor = models.CharField(max_length=100)
    cantidad_base = models.PositiveIntegerField(default=0)
    fecha_creacion = models.DateField(auto_now_add=True)

    def __str__(self):
        return self.nombre

class AjustePedido(models.Model):
    articulo = models.ForeignKey(Articulo, on_delete=models.CASCADE)
    cantidad_ajustada = models.PositiveIntegerField()
    motivo = models.TextField()
    fecha_ajuste = models.DateField(auto_now_add=True)
    comprado_fuera = models.BooleanField(default=False)
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.articulo.nombre} - {self.cantidad_ajustada} ({self.fecha_ajuste})"

class PedidoSemanal(models.Model):
    articulo = models.ForeignKey(Articulo, on_delete=models.CASCADE)
    cantidad_pedida = models.PositiveIntegerField()
    fecha_pedido = models.DateField()

    def __str__(self):
        return f"Pedido para {self.articulo.nombre} - {self.cantidad_pedida} ({self.fecha_pedido})"
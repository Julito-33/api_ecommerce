# ─────────────────────────────────────────────────────────────────────────────
# apps/orders/models.py
#
# Dos modelos que trabajan juntos:
#
# Orden     → representa una compra completa del usuario
#             guarda el total, el estado y los datos de envío
#
# ItemDeOrden → cada producto dentro de una orden
#               guarda el precio al momento de la compra
#               (importante: el precio puede cambiar después,
#               pero el historial debe conservar el precio original)
# ─────────────────────────────────────────────────────────────────────────────

from django.db import models
from apps.users.models import User
from apps.products.models import Variante


class Orden(models.Model):
    """
    Orden de compra completa.
    Se crea cuando el usuario confirma el carrito y va a pagar.
    El estado cambia a medida que avanza el proceso.
    """

    # Estados posibles de una orden durante su ciclo de vida
    ESTADOS_DE_LA_ORDEN = [
        ('pendiente',   'Pendiente de pago'),
        ('pagada',      'Pagada'),
        ('preparando',  'En preparación'),
        ('enviada',     'Enviada'),
        ('entregada',   'Entregada'),
        ('cancelada',   'Cancelada'),
    ]

    # Métodos de pago disponibles
    METODOS_DE_PAGO = [
    ('tarjeta',       'Tarjeta de crédito/débito'),
    ('transferencia', 'Transferencia bancaria'),
    ('efectivo',      'Pago en efectivo'),
]

    # El usuario que hizo la compra
    # on_delete=PROTECT para no perder el historial si se borra el usuario
    comprador = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name='ordenes_del_comprador'
    )

    estado         = models.CharField(max_length=20, choices=ESTADOS_DE_LA_ORDEN, default='pendiente')
    metodo_de_pago = models.CharField(max_length=20, choices=METODOS_DE_PAGO, blank=True)

    # Total de la orden en guaraníes al momento de la compra
    total_en_gs = models.IntegerField()

    # Datos de envío — guardamos una copia para el historial
    direccion_de_envio = models.TextField()
    ciudad_de_envio    = models.CharField(max_length=100)
    telefono_de_envio  = models.CharField(max_length=20)

    # ID que devuelve Stripe o MercadoPago al procesar el pago
    # Lo usamos para verificar el pago y para reembolsos
    id_pago_externo = models.CharField(max_length=200, blank=True)

    creada_en      = models.DateTimeField(auto_now_add=True)
    actualizada_en = models.DateTimeField(auto_now=True)

    class Meta:
        db_table         = 'ordenes'
        verbose_name     = 'Orden'
        verbose_name_plural = 'Órdenes'
        ordering         = ['-creada_en']

    def __str__(self):
        return f'Orden #{self.id} — {self.comprador.full_name} — {self.estado}'

    @property
    def cantidad_total_de_items(self):
        return sum(item.cantidad for item in self.items_de_la_orden.all())


class ItemDeOrden(models.Model):
    """
    Cada producto dentro de una orden.
    Guardamos el precio unitario al momento de la compra
    porque los precios pueden cambiar en el futuro.
    """

    orden_a_la_que_pertenece = models.ForeignKey(
        Orden,
        on_delete=models.CASCADE,
        related_name='items_de_la_orden'
    )

    variante_comprada = models.ForeignKey(
        Variante,
        on_delete=models.PROTECT,  # No borrar variantes que están en órdenes
        related_name='veces_que_fue_comprada'
    )

    cantidad              = models.IntegerField()
    precio_unitario_en_gs = models.IntegerField()  # Precio al momento de la compra
    subtotal_en_gs        = models.IntegerField()  # cantidad × precio_unitario

    class Meta:
        db_table = 'items_de_orden'

    def __str__(self):
        return f'{self.cantidad}x {self.variante_comprada.sku} en Orden #{self.orden_a_la_que_pertenece.id}'
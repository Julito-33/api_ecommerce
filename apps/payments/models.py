from django.db import models
from apps.orders.models import Orden


class Pago(models.Model):

    METODOS_DE_PAGO_DISPONIBLES = [
        ('tarjeta',      'Tarjeta de crédito/débito'),
        ('transferencia', 'Transferencia bancaria'),
        ('efectivo',     'Pago en efectivo'),
    ]

    ESTADOS_DEL_PAGO = [
        ('pendiente',  'Pendiente'),
        ('aprobado',   'Aprobado'),
        ('rechazado',  'Rechazado'),
        ('reembolsado','Reembolsado'),
    ]

    orden_pagada     = models.OneToOneField(
        Orden,
        on_delete=models.PROTECT,
        related_name='pago_de_la_orden'
    )

    metodo_utilizado  = models.CharField(max_length=20, choices=METODOS_DE_PAGO_DISPONIBLES)
    monto_cobrado_gs  = models.IntegerField()
    estado_del_pago   = models.CharField(max_length=20, choices=ESTADOS_DEL_PAGO, default='pendiente')

    # Código único generado al aprobar el pago — sirve como comprobante
    codigo_de_pago    = models.CharField(max_length=100, blank=True)

    # Datos de tarjeta — solo guardamos los últimos 4 dígitos por seguridad
    ultimos_4_digitos = models.CharField(max_length=4, blank=True)

    # Comprobante de transferencia — el usuario sube una imagen
    comprobante       = models.ImageField(upload_to='comprobantes/', blank=True, null=True)

    # Observaciones del admin al revisar el pago
    observacion_del_admin = models.TextField(blank=True)

    fecha_del_pago    = models.DateTimeField(auto_now_add=True)
    actualizado_en    = models.DateTimeField(auto_now=True)

    class Meta:
        db_table      = 'pagos'
        verbose_name  = 'Pago'
        verbose_name_plural = 'Pagos'
        ordering      = ['-fecha_del_pago']

    def __str__(self):
        return f'Pago #{self.id} — Orden #{self.orden_pagada.id} — {self.estado_del_pago}'
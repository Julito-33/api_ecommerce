from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from apps.users.models import User
from apps.products.models import Producto


class Resena(models.Model):

    # Estados de moderación — una reseña pasa por aprobación antes de publicarse
    ESTADOS_DE_MODERACION = [
        ('pendiente',  'Pendiente de revisión'),
        ('aprobada',   'Aprobada'),
        ('rechazada',  'Rechazada'),
    ]

    producto_reseñado = models.ForeignKey(
        Producto,
        on_delete=models.CASCADE,
        related_name='resenas_del_producto'
    )

    autor_de_la_resena = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='resenas_escritas_por_el_usuario'
    )

    # Calificación del 1 al 5
    calificacion = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )

    titulo_de_la_resena  = models.CharField(max_length=200)
    cuerpo_de_la_resena  = models.TextField()
    estado_de_moderacion = models.CharField(
        max_length=20,
        choices=ESTADOS_DE_MODERACION,
        default='pendiente'
    )

    escrita_en     = models.DateTimeField(auto_now_add=True)
    actualizada_en = models.DateTimeField(auto_now=True)

    #class Meta:
        # db_table         = 'resenas'
        # verbose_name     = 'Reseña'
        # verbose_name_plural = 'Reseñas'
        # ordering         = ['-escrita_en']
        # # Un usuario solo puede reseñar un producto una vez
        # unique_together  = ['producto_reseñado', 'autor_de_la_resena']

    def __str__(self):
        return f'{self.calificacion}★ — {self.producto_reseñado.nombre} por {self.autor_de_la_resena.full_name}'
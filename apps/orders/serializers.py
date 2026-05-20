# ─────────────────────────────────────────────────────────────────────────────
# apps/orders/serializers.py
#
# Tres serializers:
#
# SerializadorDeItemDeOrden  → cada producto dentro de una orden
# SerializadorDeOrden        → orden completa con todos sus items adentro
# SerializadorParaCrearOrden → valida los datos al crear una orden nueva
# ─────────────────────────────────────────────────────────────────────────────

from rest_framework import serializers
from .models import Orden, ItemDeOrden


class SerializadorDeItemDeOrden(serializers.ModelSerializer):
    """
    Convierte cada item de una orden a JSON.
    Incluye el nombre del producto y los atributos de la variante
    para que el historial sea legible sin tener que hacer otra consulta.
    """

    nombre_del_producto = serializers.CharField(
        source='variante_comprada.producto_padre.nombre',
        read_only=True
    )
    talla_comprada = serializers.CharField(
        source='variante_comprada.talla',
        read_only=True
    )
    color_comprado = serializers.CharField(
        source='variante_comprada.color',
        read_only=True
    )
    sku_comprado = serializers.CharField(
        source='variante_comprada.sku',
        read_only=True
    )

    class Meta:
        model  = ItemDeOrden
        fields = [
            'id', 'nombre_del_producto', 'talla_comprada',
            'color_comprado', 'sku_comprado',
            'cantidad', 'precio_unitario_en_gs', 'subtotal_en_gs'
        ]


class SerializadorDeOrden(serializers.ModelSerializer):
    """
    Convierte una orden completa a JSON con todos sus items anidados.
    Se usa para mostrar el detalle de una orden y el historial.
    """

    items_de_la_orden        = SerializadorDeItemDeOrden(many=True, read_only=True)
    nombre_del_comprador     = serializers.CharField(source='comprador.full_name', read_only=True)
    cantidad_total_de_items  = serializers.ReadOnlyField()

    class Meta:
        model  = Orden
        fields = [
            'id', 'nombre_del_comprador', 'estado', 'metodo_de_pago',
            'total_en_gs', 'cantidad_total_de_items',
            'direccion_de_envio', 'ciudad_de_envio', 'telefono_de_envio',
            'items_de_la_orden', 'creada_en', 'actualizada_en'
        ]


class SerializadorParaCrearOrden(serializers.Serializer):
    """
    Valida los datos necesarios para crear una orden desde el carrito.
    No hereda de ModelSerializer porque la lógica de creación
    es más compleja — la manejamos en la vista.
    """

    direccion_de_envio = serializers.CharField(max_length=500)
    ciudad_de_envio    = serializers.CharField(max_length=100)
    telefono_de_envio  = serializers.CharField(max_length=20)
    metodo_de_pago     = serializers.ChoiceField(choices=['stripe', 'mercadopago'])
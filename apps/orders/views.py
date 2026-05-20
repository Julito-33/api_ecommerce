# ─────────────────────────────────────────────────────────────────────────────
# apps/orders/views.py
#
# Endpoints del módulo de órdenes:
#
#   POST /api/ordenes/crear/        → convierte el carrito en una orden
#   GET  /api/ordenes/mis-ordenes/  → historial de órdenes del usuario
#   GET  /api/ordenes/<id>/         → detalle de una orden específica
#   PUT  /api/ordenes/<id>/estado/  → actualizar estado (solo admin)
# ─────────────────────────────────────────────────────────────────────────────

from django.db import transaction
from django.core.cache import cache
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from apps.products.models import Variante
from apps.cart.views import obtener_carrito_desde_redis, obtener_clave_del_carrito
from .models import Orden, ItemDeOrden
from .serializers import SerializadorDeOrden, SerializadorParaCrearOrden


class CrearOrdenDesdeElCarrito(APIView):
    """
    POST /api/ordenes/crear/
    Convierte el carrito del usuario en una orden real en PostgreSQL.
    
    Este proceso hace varias cosas en secuencia dentro de una transacción:
    1. Verifica que el carrito no esté vacío
    2. Verifica que cada variante tenga stock suficiente
    3. Crea la orden con todos sus items
    4. Descuenta el stock de cada variante
    5. Vacía el carrito en Redis
    
    Todo esto ocurre en una transacción — si algo falla,
    se revierte todo y no queda nada a medias.
    """
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request):
        # Validar los datos de envío y método de pago
        serializador_de_envio = SerializadorParaCrearOrden(data=request.data)
        if not serializador_de_envio.is_valid():
            return Response(
                serializador_de_envio.errors,
                status=status.HTTP_400_BAD_REQUEST
            )

        # Obtener el carrito actual del usuario desde Redis
        carrito_del_comprador = obtener_carrito_desde_redis(request.user.id)

        # Verificar que el carrito no esté vacío
        if not carrito_del_comprador:
            return Response(
                {'error': 'Tu carrito está vacío. Agregá productos antes de confirmar la compra'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Verificar stock de cada item antes de crear la orden
        for id_variante, datos_del_item in carrito_del_comprador.items():
            try:
                variante_a_verificar = Variante.objects.get(id=id_variante)
            except Variante.DoesNotExist:
                return Response(
                    {'error': f'El producto {datos_del_item["nombre_producto"]} ya no está disponible'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            if variante_a_verificar.stock < datos_del_item['cantidad']:
                return Response(
                    {
                        'error': f'Stock insuficiente para {datos_del_item["nombre_producto"]}. '
                                 f'Solo quedan {variante_a_verificar.stock} unidades'
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )

        # Calcular el total de la orden
        total_de_la_compra = sum(
            datos['precio_unitario'] * datos['cantidad']
            for datos in carrito_del_comprador.values()
        )

        # Crear la orden en PostgreSQL
        orden_nueva = Orden.objects.create(
            comprador          = request.user,
            estado             = 'pendiente',
            metodo_de_pago     = serializador_de_envio.validated_data['metodo_de_pago'],
            total_en_gs        = total_de_la_compra,
            direccion_de_envio = serializador_de_envio.validated_data['direccion_de_envio'],
            ciudad_de_envio    = serializador_de_envio.validated_data['ciudad_de_envio'],
            telefono_de_envio  = serializador_de_envio.validated_data['telefono_de_envio'],
        )

        # Crear cada item de la orden y descontar el stock
        for id_variante, datos_del_item in carrito_del_comprador.items():
            variante_comprada = Variante.objects.get(id=id_variante)

            # Crear el item de la orden con el precio actual
            ItemDeOrden.objects.create(
                orden_a_la_que_pertenece = orden_nueva,
                variante_comprada        = variante_comprada,
                cantidad                 = datos_del_item['cantidad'],
                precio_unitario_en_gs    = datos_del_item['precio_unitario'],
                subtotal_en_gs           = datos_del_item['precio_unitario'] * datos_del_item['cantidad'],
            )

            # Descontar el stock de la variante
            variante_comprada.stock -= datos_del_item['cantidad']
            variante_comprada.save()

        # Vaciar el carrito en Redis ahora que la orden fue creada
        cache.delete(obtener_clave_del_carrito(request.user.id))

        return Response(
            SerializadorDeOrden(orden_nueva).data,
            status=status.HTTP_201_CREATED
        )


class HistorialDeOrdenes(APIView):
    """
    GET /api/ordenes/mis-ordenes/
    Devuelve todas las órdenes del usuario autenticado.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        ordenes_del_usuario = Orden.objects.filter(
            comprador=request.user
        ).prefetch_related('items_de_la_orden__variante_comprada__producto_padre')

        serializador = SerializadorDeOrden(ordenes_del_usuario, many=True)
        return Response(serializador.data)


class DetalleDeOrden(APIView):
    """
    GET /api/ordenes/<id_de_la_orden>/
    Devuelve el detalle completo de una orden específica.
    El usuario solo puede ver sus propias órdenes.
    Los admins pueden ver cualquier orden.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, id_de_la_orden):
        try:
            # Si es admin puede ver cualquier orden
            # Si es cliente solo puede ver las suyas
            if request.user.is_admin:
                orden_solicitada = Orden.objects.prefetch_related(
                    'items_de_la_orden__variante_comprada__producto_padre'
                ).get(id=id_de_la_orden)
            else:
                orden_solicitada = Orden.objects.prefetch_related(
                    'items_de_la_orden__variante_comprada__producto_padre'
                ).get(id=id_de_la_orden, comprador=request.user)

        except Orden.DoesNotExist:
            return Response(
                {'error': 'La orden no existe o no tenés permiso para verla'},
                status=status.HTTP_404_NOT_FOUND
            )

        serializador = SerializadorDeOrden(orden_solicitada)
        return Response(serializador.data)


class ActualizarEstadoDeOrden(APIView):
    """
    PUT /api/ordenes/<id_de_la_orden>/estado/
    Actualiza el estado de una orden. Solo administradores.
    Ejemplo: cambiar de 'pagada' a 'enviada' cuando se despacha el pedido.
    """
    permission_classes = [IsAuthenticated]

    def put(self, request, id_de_la_orden):
        if not request.user.is_admin:
            return Response(
                {'error': 'Solo los administradores pueden actualizar el estado de las órdenes'},
                status=status.HTTP_403_FORBIDDEN
            )

        estado_nuevo = request.data.get('estado')
        estados_validos = ['pendiente', 'pagada', 'preparando', 'enviada', 'entregada', 'cancelada']

        if estado_nuevo not in estados_validos:
            return Response(
                {'error': f'Estado inválido. Los estados válidos son: {", ".join(estados_validos)}'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            orden_a_actualizar = Orden.objects.get(id=id_de_la_orden)
        except Orden.DoesNotExist:
            return Response(
                {'error': 'La orden no existe'},
                status=status.HTTP_404_NOT_FOUND
            )

        orden_a_actualizar.estado = estado_nuevo
        orden_a_actualizar.save()

        return Response({
            'mensaje': f'Orden #{id_de_la_orden} actualizada a estado "{estado_nuevo}"',
            'orden':   SerializadorDeOrden(orden_a_actualizar).data
        })
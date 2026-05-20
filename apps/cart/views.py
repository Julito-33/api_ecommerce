# ─────────────────────────────────────────────────────────────────────────────
# apps/cart/views.py
#
# El carrito vive en Redis, no en PostgreSQL.
# La clave en Redis es: "carrito_del_usuario_{id_del_usuario}"
# El valor es un diccionario JSON con todos los items del carrito.
#
# Endpoints:
#   GET    /api/carrito/           → ver el carrito actual
#   POST   /api/carrito/agregar/   → agregar un item al carrito
#   PUT    /api/carrito/actualizar/→ cambiar cantidad de un item
#   DELETE /api/carrito/quitar/    → quitar un item del carrito
#   DELETE /api/carrito/vaciar/    → vaciar todo el carrito
# ─────────────────────────────────────────────────────────────────────────────

import json
from django.core.cache import cache
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from apps.products.models import Variante


# Tiempo de vida del carrito en Redis: 7 días en segundos
TIEMPO_DE_VIDA_DEL_CARRITO = 60 * 60 * 24 * 7


def obtener_clave_del_carrito(id_del_usuario):
    """
    Genera la clave única de Redis para el carrito de un usuario.
    Ejemplo: "carrito_del_usuario_5"
    Así cada usuario tiene su propio carrito separado.
    """
    return f"carrito_del_usuario_{id_del_usuario}"


def obtener_carrito_desde_redis(id_del_usuario):
    """
    Lee el carrito de Redis y lo devuelve como diccionario.
    Si el carrito no existe todavía, devuelve un diccionario vacío.
    """
    clave_del_carrito = obtener_clave_del_carrito(id_del_usuario)
    carrito_guardado  = cache.get(clave_del_carrito)
    return carrito_guardado if carrito_guardado else {}


def guardar_carrito_en_redis(id_del_usuario, contenido_del_carrito):
    """
    Guarda el carrito actualizado en Redis.
    Reinicia el tiempo de vida cada vez que el usuario lo modifica.
    """
    clave_del_carrito = obtener_clave_del_carrito(id_del_usuario)
    cache.set(clave_del_carrito, contenido_del_carrito, TIEMPO_DE_VIDA_DEL_CARRITO)


def calcular_total_del_carrito(contenido_del_carrito):
    """
    Suma el total del carrito multiplicando precio × cantidad de cada item.
    Devuelve el total en guaraníes.
    """
    total_acumulado = 0
    for id_variante, datos_del_item in contenido_del_carrito.items():
        total_acumulado += datos_del_item['precio_unitario'] * datos_del_item['cantidad']
    return total_acumulado


class VerCarrito(APIView):
    """
    GET /api/carrito/
    Devuelve todos los items del carrito con el total calculado.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        carrito_actual = obtener_carrito_desde_redis(request.user.id)

        return Response({
            'items':          list(carrito_actual.values()),
            'total_items':    sum(item['cantidad'] for item in carrito_actual.values()),
            'total_en_gs':    calcular_total_del_carrito(carrito_actual),
        })


class AgregarAlCarrito(APIView):
    """
    POST /api/carrito/agregar/
    Agrega una variante al carrito o aumenta su cantidad si ya existe.
    Verifica que haya stock suficiente antes de agregar.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        id_de_variante      = request.data.get('id_variante')
        cantidad_a_agregar  = int(request.data.get('cantidad', 1))

        # Validar que se envió el id de la variante
        if not id_de_variante:
            return Response(
                {'error': 'El campo id_variante es obligatorio'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Buscar la variante en PostgreSQL para verificar stock y precio
        try:
            variante_solicitada = Variante.objects.select_related(
                'producto_padre'
            ).get(id=id_de_variante, esta_activa=True)
        except Variante.DoesNotExist:
            return Response(
                {'error': 'La variante solicitada no existe o no está disponible'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Obtener el carrito actual del usuario
        carrito_actual = obtener_carrito_desde_redis(request.user.id)

        # Calcular cuántas unidades ya tiene en el carrito
        clave_del_item      = str(id_de_variante)
        cantidad_en_carrito = carrito_actual.get(clave_del_item, {}).get('cantidad', 0)
        cantidad_total      = cantidad_en_carrito + cantidad_a_agregar

        # Verificar que no supere el stock disponible
        if cantidad_total > variante_solicitada.stock:
            return Response(
                {
                    'error': f'Stock insuficiente. Solo hay {variante_solicitada.stock} unidades disponibles'
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        # Agregar o actualizar el item en el carrito
        carrito_actual[clave_del_item] = {
            'id_variante':     variante_solicitada.id,
            'nombre_producto': variante_solicitada.producto_padre.nombre,
            'talla':           variante_solicitada.talla,
            'color':           variante_solicitada.color,
            'sku':             variante_solicitada.sku,
            'precio_unitario': variante_solicitada.precio,
            'cantidad':        cantidad_total,
            'subtotal':        variante_solicitada.precio * cantidad_total,
        }

        guardar_carrito_en_redis(request.user.id, carrito_actual)

        return Response({
            'mensaje':     f'{variante_solicitada.producto_padre.nombre} agregado al carrito',
            'carrito':     list(carrito_actual.values()),
            'total_en_gs': calcular_total_del_carrito(carrito_actual),
        }, status=status.HTTP_200_OK)


class ActualizarCantidadEnCarrito(APIView):
    """
    PUT /api/carrito/actualizar/
    Cambia la cantidad de un item ya existente en el carrito.
    Si la cantidad nueva es 0, quita el item del carrito.
    """
    permission_classes = [IsAuthenticated]

    def put(self, request):
        id_de_variante  = str(request.data.get('id_variante'))
        cantidad_nueva  = int(request.data.get('cantidad', 1))

        carrito_actual = obtener_carrito_desde_redis(request.user.id)

        # Verificar que el item existe en el carrito
        if id_de_variante not in carrito_actual:
            return Response(
                {'error': 'Ese producto no está en tu carrito'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Si la cantidad nueva es 0, quitamos el item directamente
        if cantidad_nueva == 0:
            del carrito_actual[id_de_variante]
            guardar_carrito_en_redis(request.user.id, carrito_actual)
            return Response({'mensaje': 'Producto quitado del carrito'})

        # Verificar stock antes de actualizar
        try:
            variante_solicitada = Variante.objects.get(id=id_de_variante)
        except Variante.DoesNotExist:
            return Response(
                {'error': 'La variante no existe'},
                status=status.HTTP_404_NOT_FOUND
            )

        if cantidad_nueva > variante_solicitada.stock:
            return Response(
                {'error': f'Solo hay {variante_solicitada.stock} unidades disponibles'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Actualizar cantidad y subtotal
        carrito_actual[id_de_variante]['cantidad'] = cantidad_nueva
        carrito_actual[id_de_variante]['subtotal'] = (
            carrito_actual[id_de_variante]['precio_unitario'] * cantidad_nueva
        )

        guardar_carrito_en_redis(request.user.id, carrito_actual)

        return Response({
            'mensaje':     'Carrito actualizado',
            'carrito':     list(carrito_actual.values()),
            'total_en_gs': calcular_total_del_carrito(carrito_actual),
        })


class QuitarDelCarrito(APIView):
    """
    DELETE /api/carrito/quitar/
    Quita un item específico del carrito.
    """
    permission_classes = [IsAuthenticated]

    def delete(self, request):
        id_de_variante = str(request.data.get('id_variante'))
        carrito_actual = obtener_carrito_desde_redis(request.user.id)

        if id_de_variante not in carrito_actual:
            return Response(
                {'error': 'Ese producto no está en tu carrito'},
                status=status.HTTP_404_NOT_FOUND
            )

        nombre_del_producto = carrito_actual[id_de_variante]['nombre_producto']
        del carrito_actual[id_de_variante]

        guardar_carrito_en_redis(request.user.id, carrito_actual)

        return Response({
            'mensaje':     f'{nombre_del_producto} quitado del carrito',
            'carrito':     list(carrito_actual.values()),
            'total_en_gs': calcular_total_del_carrito(carrito_actual),
        })


class VaciarCarrito(APIView):
    """
    DELETE /api/carrito/vaciar/
    Elimina todos los items del carrito de una vez.
    Se usa después de confirmar una orden.
    """
    permission_classes = [IsAuthenticated]

    def delete(self, request):
        clave_del_carrito = obtener_clave_del_carrito(request.user.id)
        cache.delete(clave_del_carrito)

        return Response({'mensaje': 'Tu carrito fue vaciado correctamente'})
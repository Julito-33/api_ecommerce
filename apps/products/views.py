# ─────────────────────────────────────────────────────────────────────────────
# apps/products/views.py
#
# Endpoints del módulo de productos:
#
# PÚBLICO (sin token):
#   GET /api/productos/           → listar productos activos con filtros
#   GET /api/productos/<slug>/    → ver detalle de un producto
#   GET /api/productos/categorias/→ listar todas las categorías
#
# PRIVADO (solo admin):
#   POST   /api/productos/crear/          → crear producto nuevo
#   PUT    /api/productos/<slug>/editar/  → editar producto
#   DELETE /api/productos/<slug>/borrar/  → desactivar producto
#   POST   /api/productos/variantes/crear/→ agregar variante a un producto
#   PUT    /api/productos/variantes/<id>/ → editar variante y su stock
# ─────────────────────────────────────────────────────────────────────────────

from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny, IsAdminUser
from django.shortcuts import get_object_or_404

from .models import Categoria, Producto, Variante
from .serializers import (
    SerializadorDeProducto,
    SerializadorDeCategoria,
    SerializadorDeVariante,
    SerializadorParaCrearProducto,
    SerializadorParaCrearVariante,
)


class ListaDeCategorias(APIView):
    """
    GET /api/productos/categorias/
    Devuelve todas las categorías con su cantidad de productos.
    Público — cualquiera puede verlo sin token.
    """
    permission_classes = [AllowAny]

    def get(self, request):
        todas_las_categorias = Categoria.objects.all()
        serializador = SerializadorDeCategoria(todas_las_categorias, many=True)
        return Response(serializador.data)


class ListaDeProductos(APIView):
    """
    GET /api/productos/
    Lista todos los productos activos.
    Soporta filtros por query params:
      ?categoria=remeras
      ?precio_min=100000&precio_max=500000
      ?buscar=naranja
    Público — cualquiera puede verlo sin token.
    """
    permission_classes = [AllowAny]

    def get(self, request):
        # Empezamos con todos los productos activos
        productos_encontrados = Producto.objects.filter(esta_activo=True)

        # Filtro por categoría usando el slug
        slug_de_categoria = request.query_params.get('categoria')
        if slug_de_categoria:
            productos_encontrados = productos_encontrados.filter(
                categoria__slug=slug_de_categoria
            )

        # Filtro por búsqueda de texto en nombre y descripción
        texto_buscado = request.query_params.get('buscar')
        if texto_buscado:
            productos_encontrados = productos_encontrados.filter(
                nombre__icontains=texto_buscado
            )

        # Filtro por rango de precio mínimo
        precio_minimo = request.query_params.get('precio_min')
        if precio_minimo:
            productos_encontrados = productos_encontrados.filter(
                variantes_del_producto__precio__gte=precio_minimo
            ).distinct()

        # Filtro por rango de precio máximo
        precio_maximo = request.query_params.get('precio_max')
        if precio_maximo:
            productos_encontrados = productos_encontrados.filter(
                variantes_del_producto__precio__lte=precio_maximo
            ).distinct()

        serializador = SerializadorDeProducto(productos_encontrados, many=True)
        return Response(serializador.data)


class DetalleDeProducto(APIView):
    """
    GET /api/productos/<slug>/
    Devuelve el detalle completo de un producto con todas sus variantes.
    Público — cualquiera puede verlo sin token.
    """
    permission_classes = [AllowAny]

    def get(self, request, slug_del_producto):
        producto_solicitado = get_object_or_404(
            Producto,
            slug=slug_del_producto,
            esta_activo=True
        )
        serializador = SerializadorDeProducto(producto_solicitado)
        return Response(serializador.data)


class CrearProducto(APIView):
    """
    POST /api/productos/crear/
    Crea un producto nuevo. Solo administradores.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        # Verificamos que el usuario sea admin antes de crear
        if not request.user.is_admin:
            return Response(
                {'error': 'Solo los administradores pueden crear productos'},
                status=status.HTTP_403_FORBIDDEN
            )

        serializador = SerializadorParaCrearProducto(data=request.data)

        if serializador.is_valid():
            producto_nuevo = serializador.save()
            return Response(
                SerializadorDeProducto(producto_nuevo).data,
                status=status.HTTP_201_CREATED
            )

        return Response(serializador.errors, status=status.HTTP_400_BAD_REQUEST)


class EditarProducto(APIView):
    """
    PUT /api/productos/<slug>/editar/
    Edita un producto existente. Solo administradores.
    """
    permission_classes = [IsAuthenticated]

    def put(self, request, slug_del_producto):
        if not request.user.is_admin:
            return Response(
                {'error': 'Solo los administradores pueden editar productos'},
                status=status.HTTP_403_FORBIDDEN
            )

        producto_a_editar = get_object_or_404(Producto, slug=slug_del_producto)
        serializador = SerializadorParaCrearProducto(
            producto_a_editar,
            data=request.data,
            partial=True
        )

        if serializador.is_valid():
            producto_actualizado = serializador.save()
            return Response(SerializadorDeProducto(producto_actualizado).data)

        return Response(serializador.errors, status=status.HTTP_400_BAD_REQUEST)


class DesactivarProducto(APIView):
    """
    DELETE /api/productos/<slug>/borrar/
    No borra el producto de la DB — lo desactiva.
    Así conservamos el historial de órdenes que lo incluyen.
    Solo administradores.
    """
    permission_classes = [IsAuthenticated]

    def delete(self, request, slug_del_producto):
        if not request.user.is_admin:
            return Response(
                {'error': 'Solo los administradores pueden desactivar productos'},
                status=status.HTTP_403_FORBIDDEN
            )

        producto_a_desactivar = get_object_or_404(Producto, slug=slug_del_producto)
        producto_a_desactivar.esta_activo = False
        producto_a_desactivar.save()

        return Response(
            {'mensaje': f'Producto "{producto_a_desactivar.nombre}" desactivado correctamente'},
            status=status.HTTP_200_OK
        )


class CrearVariante(APIView):
    """
    POST /api/productos/variantes/crear/
    Agrega una variante nueva a un producto existente.
    Solo administradores.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        if not request.user.is_admin:
            return Response(
                {'error': 'Solo los administradores pueden agregar variantes'},
                status=status.HTTP_403_FORBIDDEN
            )

        serializador = SerializadorParaCrearVariante(data=request.data)

        if serializador.is_valid():
            variante_nueva = serializador.save()
            return Response(
                SerializadorDeVariante(variante_nueva).data,
                status=status.HTTP_201_CREATED
            )

        return Response(serializador.errors, status=status.HTTP_400_BAD_REQUEST)


class EditarVariante(APIView):
    """
    PUT /api/productos/variantes/<id>/
    Edita una variante — principalmente para actualizar stock y precio.
    Solo administradores.
    """
    permission_classes = [IsAuthenticated]

    def put(self, request, id_de_variante):
        if not request.user.is_admin:
            return Response(
                {'error': 'Solo los administradores pueden editar variantes'},
                status=status.HTTP_403_FORBIDDEN
            )

        variante_a_editar = get_object_or_404(Variante, id=id_de_variante)
        serializador = SerializadorParaCrearVariante(
            variante_a_editar,
            data=request.data,
            partial=True
        )

        if serializador.is_valid():
            variante_actualizada = serializador.save()
            return Response(SerializadorDeVariante(variante_actualizada).data)

        return Response(serializador.errors, status=status.HTTP_400_BAD_REQUEST)
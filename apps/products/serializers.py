# ─────────────────────────────────────────────────────────────────────────────
# apps/products/serializers.py
#
# Tres serializers que convierten los modelos a JSON:
#
# SerializadorDeVariante    → datos de cada variante (talla, color, precio, stock)
# SerializadorDeProducto    → producto completo con todas sus variantes adentro
# SerializadorDeCategoria   → categoría con la cantidad de productos que tiene
# ─────────────────────────────────────────────────────────────────────────────

from rest_framework import serializers
from .models import Categoria, Producto, Variante


class SerializadorDeVariante(serializers.ModelSerializer):
    """
    Convierte una variante a JSON.
    Se usa anidado dentro del SerializadorDeProducto
    para que cada producto muestre todas sus variantes.
    """

    hay_stock_disponible = serializers.ReadOnlyField()

    class Meta:
        model  = Variante
        fields = [
            'id', 'sku', 'talla', 'color',
            'imagen', 'precio', 'stock', 'hay_stock_disponible',
            'esta_activa'
        ]


class SerializadorDeProducto(serializers.ModelSerializer):
    """
    Convierte un producto completo a JSON, incluyendo:
    - Todas sus variantes anidadas
    - El nombre de la categoría (no solo el ID)
    - Si tiene stock disponible
    - El precio mínimo entre todas sus variantes
    """

    # Anidamos las variantes directamente en la respuesta del producto
    variantes_del_producto = SerializadorDeVariante(many=True, read_only=True)

    # Mostramos el nombre de la categoría en vez de solo el ID numérico
    nombre_de_categoria = serializers.CharField(
        source='categoria.nombre',
        read_only=True
    )

    # Propiedades calculadas del modelo
    tiene_stock   = serializers.ReadOnlyField()
    precio_minimo = serializers.ReadOnlyField()

    class Meta:
        model  = Producto
        fields = [
            'id', 'nombre', 'descripcion', 'slug',
            'imagen', 'esta_activo', 'categoria', 'nombre_de_categoria',
            'variantes_del_producto', 'tiene_stock', 'precio_minimo',
            'creado_en', 'actualizado_en'
        ]


class SerializadorDeCategoria(serializers.ModelSerializer):
    """
    Convierte una categoría a JSON.
    Incluye la cantidad de productos activos que tiene,
    útil para mostrar "Remeras (24)" en el menú de la tienda.
    """

    cantidad_de_productos = serializers.SerializerMethodField()

    class Meta:
        model  = Categoria
        fields = ['id', 'nombre', 'descripcion', 'slug', 'imagen', 'cantidad_de_productos']

    def get_cantidad_de_productos(self, categoria_actual):
        # Contamos solo los productos activos de esta categoría
        return categoria_actual.productos_de_esta_categoria.filter(esta_activo=True).count()


class SerializadorParaCrearProducto(serializers.ModelSerializer):
    """
    Serializer para crear o editar un producto desde el panel admin.
    Solo los administradores llegan a usar este serializer.
    """

    class Meta:
        model  = Producto
        fields = ['nombre', 'descripcion', 'slug', 'imagen', 'categoria', 'esta_activo']


class SerializadorParaCrearVariante(serializers.ModelSerializer):
    """
    Serializer para crear o editar una variante desde el panel admin.
    Valida que el stock no sea negativo y que el precio sea mayor a cero.
    """

    class Meta:
        model  = Variante
        fields = ['producto_padre', 'sku', 'talla', 'color', 'imagen', 'precio', 'stock', 'esta_activa']

    def validate_precio(self, precio_ingresado):
        if precio_ingresado <= 0:
            raise serializers.ValidationError('El precio debe ser mayor a cero')
        return precio_ingresado

    def validate_stock(self, cantidad_de_stock):
        if cantidad_de_stock < 0:
            raise serializers.ValidationError('El stock no puede ser negativo')
        return cantidad_de_stock
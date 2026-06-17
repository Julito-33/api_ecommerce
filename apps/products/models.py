# ─────────────────────────────────────────────────────────────────────────────
# apps/products/models.py
#
# Tres modelos que trabajan juntos:
#
# Categoria → agrupa productos (ej: "Remeras", "Zapatillas")
# Producto  → el producto base (ej: "Remera Naranja")
# Variante  → cada combinación de talla/color con su propio stock y precio
#             (ej: "Remera Naranja - Talla M - Color Blanco - Stock 10")
#
# Esta estructura permite que un producto tenga múltiples variantes,
# cada una con su propio precio, stock e imagen.
# ─────────────────────────────────────────────────────────────────────────────

from django.db import models


class Categoria(models.Model):
    """
    Categoría de productos.
    Ejemplo: Remeras, Zapatillas, Accesorios, Electrónica.
    """
    nombre      = models.CharField(max_length=100, unique=True)
    descripcion = models.TextField(blank=True)
    imagen      = models.ImageField(upload_to='categorias/', blank=True, null=True)

    # slug es la versión URL de un nombre: "Remeras Deportivas" → "remeras-deportivas"
    slug        = models.SlugField(unique=True)

    creado_en   = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table         = 'categorias'
        verbose_name     = 'Categoría'
        verbose_name_plural = 'Categorías'
        ordering         = ['nombre']

    def __str__(self):
        return self.nombre


class Producto(models.Model):
    """
    Producto base de la tienda.
    Contiene la información general que comparten todas las variantes:
    nombre, descripción, categoría, imagen principal.
    El precio y el stock viven en cada Variante, no aquí.
    """

    categoria   = models.ForeignKey(
        Categoria,
        on_delete=models.PROTECT,   # No permite borrar una categoría que tiene productos
        related_name='productos_de_esta_categoria'
    )

    nombre      = models.CharField(max_length=200)
    descripcion = models.TextField()
    imagen      = models.ImageField(upload_to='productos/', blank=True, null=True)
    slug        = models.SlugField(unique=True)

    # Si es False, el producto no aparece en la tienda aunque exista en la DB
    esta_activo = models.BooleanField(default=True)

    creado_en      = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        db_table         = 'productos'
        verbose_name     = 'Producto'
        verbose_name_plural = 'Productos'
        ordering         = ['-creado_en']

    def __str__(self):
        return self.nombre

    @property
    def tiene_stock(self):
        """
        Devuelve True si al menos una variante tiene stock disponible.
        Se usa en el frontend para mostrar "Agotado" o "Disponible".
        """
        return self.variantes_del_producto.filter(stock__gt=0).exists()

    @property
    def precio_minimo(self):
        """
        Devuelve el precio más bajo entre todas las variantes activas.
        Se usa para mostrar "Desde Gs. 150.000" en el catálogo.
        """
        variante_mas_barata = self.variantes_del_producto.filter(
            esta_activa=True
        ).order_by('precio').first()

        return variante_mas_barata.precio if variante_mas_barata else None


class Variante(models.Model):
    """
    Variante de un producto.
    Cada combinación única de atributos es una variante separada.
    Ejemplo para "Remera Naranja":
      - Variante 1: Talla S, Color Blanco, Precio 150.000, Stock 5
      - Variante 2: Talla M, Color Blanco, Precio 150.000, Stock 10
      - Variante 3: Talla M, Color Negro,  Precio 160.000, Stock 3
    """

    producto_padre = models.ForeignKey(
        Producto,
        on_delete=models.CASCADE,   # Si se borra el producto, se borran sus variantes
        related_name='variantes_del_producto'
    )

    # SKU = Stock Keeping Unit — código único para identificar cada variante
    # Ejemplo: "REMNARANJA-M-BLANCO"
    sku    = models.CharField(max_length=100, unique=True)
    talla  = models.CharField(max_length=20, blank=True)   # S, M, L, XL, 38, 39...
    color  = models.CharField(max_length=50, blank=True)   # Rojo, Azul, Negro...
    imagen = models.ImageField(upload_to='variantes/', blank=True, null=True)

    # Precio en guaraníes (sin decimales, por eso usamos IntegerField)
    precio = models.IntegerField()

    # Stock actual disponible para venta
    stock  = models.IntegerField(default=0)

    esta_activa = models.BooleanField(default=True)

    creado_en      = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        db_table         = 'variantes'
        verbose_name     = 'Variante'
        verbose_name_plural = 'Variantes'

    def __str__(self):
        return f'{self.producto_padre.nombre} — {self.talla} {self.color} (SKU: {self.sku})'

    @property
    def hay_stock_disponible(self):
        return self.stock > 0
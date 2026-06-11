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
    nombre      = models.CharField(max_length=100, unique=True)
    descripcion = models.TextField(blank=True)
    imagen      = models.URLField(max_length=500, blank=True, null=True)
    slug        = models.SlugField(unique=True)
    creado_en   = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table            = 'categorias'
        verbose_name        = 'Categoría'
        verbose_name_plural = 'Categorías'
        ordering            = ['nombre']

    def __str__(self):
        return self.nombre


class Producto(models.Model):
    categoria   = models.ForeignKey(
        Categoria,
        on_delete=models.PROTECT,
        related_name='productos_de_esta_categoria'
    )
    nombre      = models.CharField(max_length=200)
    descripcion = models.TextField()
    imagen      = models.URLField(max_length=500, blank=True, null=True)
    slug        = models.SlugField(unique=True)
    esta_activo = models.BooleanField(default=True)
    creado_en      = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        db_table            = 'productos'
        verbose_name        = 'Producto'
        verbose_name_plural = 'Productos'
        ordering            = ['-creado_en']

    def __str__(self):
        return self.nombre

    @property
    def tiene_stock(self):
        return self.variantes_del_producto.filter(stock__gt=0).exists()

    @property
    def precio_minimo(self):
        variante_mas_barata = self.variantes_del_producto.filter(
            esta_activa=True
        ).order_by('precio').first()
        return variante_mas_barata.precio if variante_mas_barata else None


class Variante(models.Model):
    producto_padre = models.ForeignKey(
        Producto,
        on_delete=models.CASCADE,
        related_name='variantes_del_producto'
    )
    sku         = models.CharField(max_length=100, unique=True)
    talla       = models.CharField(max_length=20, blank=True)
    color       = models.CharField(max_length=50, blank=True)
    imagen      = models.URLField(max_length=500, blank=True, null=True)
    precio      = models.IntegerField()
    stock       = models.IntegerField(default=0)
    esta_activa = models.BooleanField(default=True)
    creado_en      = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        db_table            = 'variantes'
        verbose_name        = 'Variante'
        verbose_name_plural = 'Variantes'

    def __str__(self):
        return f'{self.producto_padre.nombre} — {self.talla} {self.color} (SKU: {self.sku})'

    @property
    def hay_stock_disponible(self):
        return self.stock > 0
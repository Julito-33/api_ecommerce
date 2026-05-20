from django.contrib import admin
from .models import Categoria, Producto, Variante


class VariantesDelProducto(admin.TabularInline):
    # Muestra las variantes directamente dentro del formulario del producto
    model  = Variante
    extra  = 1  # Un formulario vacío extra para agregar variante nueva
    fields = ['sku', 'talla', 'color', 'precio', 'stock', 'esta_activa']


@admin.register(Categoria)
class PanelDeCategorias(admin.ModelAdmin):
    list_display  = ['nombre', 'slug']
    search_fields = ['nombre']
    prepopulated_fields = {'slug': ('nombre',)}  # El slug se genera solo desde el nombre


@admin.register(Producto)
class PanelDeProductos(admin.ModelAdmin):
    list_display  = ['nombre', 'categoria', 'esta_activo', 'tiene_stock', 'precio_minimo', 'creado_en']
    list_filter   = ['esta_activo', 'categoria']
    search_fields = ['nombre', 'descripcion']
    prepopulated_fields = {'slug': ('nombre',)}
    inlines       = [VariantesDelProducto]  # Las variantes aparecen dentro del producto


@admin.register(Variante)
class PanelDeVariantes(admin.ModelAdmin):
    list_display  = ['sku', 'producto_padre', 'talla', 'color', 'precio', 'stock', 'esta_activa']
    list_filter   = ['esta_activa', 'talla', 'color']
    search_fields = ['sku', 'producto_padre__nombre']
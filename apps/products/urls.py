# ─────────────────────────────────────────────────────────────────────────────
# apps/products/urls.py
#
# Rutas del módulo de productos.
# ─────────────────────────────────────────────────────────────────────────────

from django.urls import path
from . import views

urlpatterns = [
    # ── Rutas públicas ────────────────────────────────────────────────────────
    # Listar todas las categorías
    path('categorias/', views.ListaDeCategorias.as_view(), name='lista_de_categorias'),

    # Listar productos con filtros opcionales
    path('', views.ListaDeProductos.as_view(), name='lista_de_productos'),

    # Ver detalle de un producto por su slug
    path('<slug:slug_del_producto>/', views.DetalleDeProducto.as_view(), name='detalle_de_producto'),

    # ── Rutas de administración ───────────────────────────────────────────────
    # Crear producto nuevo
    path('crear/', views.CrearProducto.as_view(), name='crear_producto'),

    # Editar producto existente
    path('<slug:slug_del_producto>/editar/', views.EditarProducto.as_view(), name='editar_producto'),

    # Desactivar producto
    path('<slug:slug_del_producto>/borrar/', views.DesactivarProducto.as_view(), name='desactivar_producto'),

    # Crear variante nueva
    path('variantes/crear/', views.CrearVariante.as_view(), name='crear_variante'),

    # Editar variante existente
    path('variantes/<int:id_de_variante>/', views.EditarVariante.as_view(), name='editar_variante'),
]
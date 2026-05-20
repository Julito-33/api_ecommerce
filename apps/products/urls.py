# ─────────────────────────────────────────────────────────────────────────────
# apps/products/urls.py
#
# IMPORTANTE: el orden de las rutas importa en Django.
# Las rutas específicas (crear/, variantes/crear/) van ANTES
# que las rutas con parámetros (<slug:slug_del_producto>/)
# para que Django no las confunda.
# ─────────────────────────────────────────────────────────────────────────────

from django.urls import path
from . import views

urlpatterns = [
    # ── Rutas fijas — van primero para evitar conflictos ──────────────────────
    path('categorias/',        views.ListaDeCategorias.as_view(), name='lista_de_categorias'),
    path('crear/',             views.CrearProducto.as_view(),     name='crear_producto'),
    path('variantes/crear/',   views.CrearVariante.as_view(),     name='crear_variante'),

    # ── Rutas con parámetros — van después ────────────────────────────────────
    path('',                                        views.ListaDeProductos.as_view(),  name='lista_de_productos'),
    path('<slug:slug_del_producto>/',               views.DetalleDeProducto.as_view(), name='detalle_de_producto'),
    path('<slug:slug_del_producto>/editar/',        views.EditarProducto.as_view(),    name='editar_producto'),
    path('<slug:slug_del_producto>/borrar/',        views.DesactivarProducto.as_view(),name='desactivar_producto'),
    path('variantes/<int:id_de_variante>/',         views.EditarVariante.as_view(),    name='editar_variante'),
]
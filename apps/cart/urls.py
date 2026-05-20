# ─────────────────────────────────────────────────────────────────────────────
# apps/cart/urls.py
#
# Rutas del módulo del carrito.
# Todos los endpoints requieren token JWT — un carrito es personal.
# ─────────────────────────────────────────────────────────────────────────────

from django.urls import path
from . import views

urlpatterns = [
    # Ver el carrito actual
    path('', views.VerCarrito.as_view(), name='ver_carrito'),

    # Agregar un item al carrito
    path('agregar/', views.AgregarAlCarrito.as_view(), name='agregar_al_carrito'),

    # Cambiar la cantidad de un item
    path('actualizar/', views.ActualizarCantidadEnCarrito.as_view(), name='actualizar_carrito'),

    # Quitar un item específico
    path('quitar/', views.QuitarDelCarrito.as_view(), name='quitar_del_carrito'),

    # Vaciar todo el carrito
    path('vaciar/', views.VaciarCarrito.as_view(), name='vaciar_carrito'),
]
# ─────────────────────────────────────────────────────────────────────────────
# apps/orders/urls.py
#
# Rutas del módulo de órdenes.
# Todos los endpoints requieren token JWT.
# ─────────────────────────────────────────────────────────────────────────────

from django.urls import path
from . import views

urlpatterns = [
    # Convertir el carrito en una orden
    path('crear/', views.CrearOrdenDesdeElCarrito.as_view(), name='crear_orden'),

    # Historial de órdenes del usuario autenticado
    path('mis-ordenes/', views.HistorialDeOrdenes.as_view(), name='historial_de_ordenes'),

    # Detalle de una orden específica
    path('<int:id_de_la_orden>/', views.DetalleDeOrden.as_view(), name='detalle_de_orden'),

    # Actualizar estado de una orden (solo admin)
    path('<int:id_de_la_orden>/estado/', views.ActualizarEstadoDeOrden.as_view(), name='actualizar_estado_de_orden'),
]
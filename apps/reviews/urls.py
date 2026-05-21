from django.urls import path
from . import views

urlpatterns = [
    # Reseñas pendientes de moderación (solo admin)
    path('pendientes/', views.ReseñasPendientes.as_view(), name='resenas_pendientes'),

    # Ver reseñas aprobadas de un producto
    path('<slug:slug_del_producto>/', views.ResenasDeUnProducto.as_view(), name='resenas_del_producto'),

    # Escribir una reseña sobre un producto
    path('<slug:slug_del_producto>/escribir/', views.EscribirResena.as_view(), name='escribir_resena'),

    # Aprobar o rechazar una reseña (solo admin)
    path('<int:id_de_la_resena>/moderar/', views.ModerarResena.as_view(), name='moderar_resena'),
]
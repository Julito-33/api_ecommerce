from django.urls import path
from . import views

urlpatterns = [
    # Descargar factura PDF de una orden pagada
    path('<int:id_de_la_orden>/', views.DescargarFacturaPDF.as_view(), name='descargar_factura'),
]
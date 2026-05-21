from django.urls import path
from . import views

urlpatterns = [
    # Pagar con tarjeta de crédito/débito
    path('tarjeta/<int:id_de_la_orden>/', views.PagarConTarjeta.as_view(), name='pagar_con_tarjeta'),

    # Pagar con transferencia bancaria
    path('transferencia/<int:id_de_la_orden>/', views.PagarConTransferencia.as_view(), name='pagar_con_transferencia'),

    # Pagar en efectivo — genera código de pago
    path('efectivo/<int:id_de_la_orden>/', views.PagarEnEfectivo.as_view(), name='pagar_en_efectivo'),

    # Verificar pago de transferencia (solo admin)
    path('<int:id_del_pago>/verificar/', views.VerificarPagoDeTransferencia.as_view(), name='verificar_pago'),
]
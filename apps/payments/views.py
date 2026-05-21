import uuid
from django.db import transaction
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from apps.orders.models import Orden
from .models import Pago
from .serializers import (
    SerializadorDePago,
    SerializadorParaPagarConTarjeta,
    SerializadorParaPagarConTransferencia,
    SerializadorParaPagarEnEfectivo,
)


# ─────────────────────────────────────────────────────────────────────────────
# Tarjetas de prueba predefinidas
# En producción real aquí estaría la llamada a Stripe o MercadoPago.
# Para el proyecto académico simulamos la respuesta del banco.
# ─────────────────────────────────────────────────────────────────────────────
TARJETAS_QUE_SIEMPRE_SE_APRUEBAN = [
    '4111111111111111',  # Visa de prueba
    '5500000000000004',  # Mastercard de prueba
]

TARJETAS_QUE_SIEMPRE_SE_RECHAZAN = [
    '4000000000000002',  # Tarjeta bloqueada
    '4000000000000069',  # Tarjeta vencida
]


def simular_procesamiento_de_tarjeta(numero_de_tarjeta):
    """
    Simula la respuesta del banco al procesar una tarjeta.
    En un sistema real, aquí se haría la llamada a la pasarela de pago.
    """
    if numero_de_tarjeta in TARJETAS_QUE_SIEMPRE_SE_APRUEBAN:
        return {'aprobado': True, 'mensaje': 'Pago aprobado por el banco'}

    if numero_de_tarjeta in TARJETAS_QUE_SIEMPRE_SE_RECHAZAN:
        return {'aprobado': False, 'mensaje': 'Tarjeta rechazada por el banco'}

    # Cualquier otra tarjeta válida se aprueba en modo simulación
    return {'aprobado': True, 'mensaje': 'Pago aprobado'}


def generar_codigo_de_pago():
    """
    Genera un código único para identificar cada pago aprobado.
    Ejemplo: PAGO-A1B2C3D4
    Este código aparece en la factura como comprobante.
    """
    codigo_unico = str(uuid.uuid4()).upper()[:8]
    return f'PAGO-{codigo_unico}'


class PagarConTarjeta(APIView):
    """
    POST /api/pagos/tarjeta/<id_de_la_orden>/
    Procesa el pago de una orden con tarjeta de crédito o débito.
    """
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request, id_de_la_orden):
        # Verificar que la orden existe y pertenece al usuario
        try:
            orden_a_pagar = Orden.objects.get(
                id=id_de_la_orden,
                comprador=request.user
            )
        except Orden.DoesNotExist:
            return Response(
                {'error': 'La orden no existe o no te pertenece'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Verificar que la orden está pendiente de pago
        if orden_a_pagar.estado != 'pendiente':
            return Response(
                {'error': f'Esta orden ya fue procesada — estado actual: {orden_a_pagar.estado}'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Verificar que la orden no tiene ya un pago registrado
        if hasattr(orden_a_pagar, 'pago_de_la_orden'):
            return Response(
                {'error': 'Esta orden ya tiene un pago registrado'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Validar los datos de la tarjeta
        serializador_de_tarjeta = SerializadorParaPagarConTarjeta(data=request.data)
        if not serializador_de_tarjeta.is_valid():
            return Response(
                serializador_de_tarjeta.errors,
                status=status.HTTP_400_BAD_REQUEST
            )

        datos_de_la_tarjeta  = serializador_de_tarjeta.validated_data
        numero_de_la_tarjeta = datos_de_la_tarjeta['numero_de_tarjeta']

        # Simular el procesamiento con el banco
        respuesta_del_banco = simular_procesamiento_de_tarjeta(numero_de_la_tarjeta)

        if respuesta_del_banco['aprobado']:
            # Pago aprobado — crear el registro y actualizar la orden
            codigo_generado = generar_codigo_de_pago()

            pago_registrado = Pago.objects.create(
                orden_pagada      = orden_a_pagar,
                metodo_utilizado  = 'tarjeta',
                monto_cobrado_gs  = orden_a_pagar.total_en_gs,
                estado_del_pago   = 'aprobado',
                codigo_de_pago    = codigo_generado,
                # Solo guardamos los últimos 4 dígitos por seguridad
                ultimos_4_digitos = numero_de_la_tarjeta[-4:],
            )

            # Actualizar el estado de la orden a pagada
            orden_a_pagar.estado = 'pagada'
            orden_a_pagar.save()

            return Response({
                'mensaje':      '¡Pago procesado exitosamente!',
                'codigo_de_pago': codigo_generado,
                'pago':         SerializadorDePago(pago_registrado).data
            }, status=status.HTTP_200_OK)

        else:
            # Pago rechazado — registramos el intento fallido
            Pago.objects.create(
                orden_pagada      = orden_a_pagar,
                metodo_utilizado  = 'tarjeta',
                monto_cobrado_gs  = orden_a_pagar.total_en_gs,
                estado_del_pago   = 'rechazado',
                ultimos_4_digitos = numero_de_la_tarjeta[-4:],
            )

            return Response({
                'error': respuesta_del_banco['mensaje'],
            }, status=status.HTTP_402_PAYMENT_REQUIRED)


class PagarConTransferencia(APIView):
    """
    POST /api/pagos/transferencia/<id_de_la_orden>/
    El usuario sube el comprobante de transferencia.
    El pago queda pendiente hasta que el admin lo verifique manualmente.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, id_de_la_orden):
        try:
            orden_a_pagar = Orden.objects.get(
                id=id_de_la_orden,
                comprador=request.user
            )
        except Orden.DoesNotExist:
            return Response(
                {'error': 'La orden no existe o no te pertenece'},
                status=status.HTTP_404_NOT_FOUND
            )

        if orden_a_pagar.estado != 'pendiente':
            return Response(
                {'error': f'Esta orden ya fue procesada — estado actual: {orden_a_pagar.estado}'},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializador_de_transferencia = SerializadorParaPagarConTransferencia(data=request.data)
        if not serializador_de_transferencia.is_valid():
            return Response(
                serializador_de_transferencia.errors,
                status=status.HTTP_400_BAD_REQUEST
            )

        datos_de_la_transferencia = serializador_de_transferencia.validated_data

        # El pago queda pendiente hasta verificación manual del admin
        pago_registrado = Pago.objects.create(
            orden_pagada     = orden_a_pagar,
            metodo_utilizado = 'transferencia',
            monto_cobrado_gs = orden_a_pagar.total_en_gs,
            estado_del_pago  = 'pendiente',
            comprobante      = datos_de_la_transferencia.get('comprobante'),
            observacion_del_admin = f"Banco: {datos_de_la_transferencia['banco_de_origen']} — Ref: {datos_de_la_transferencia['numero_de_referencia']}"
        )

        return Response({
            'mensaje': 'Comprobante recibido. Tu pago será verificado en las próximas horas.',
            'pago':    SerializadorDePago(pago_registrado).data
        }, status=status.HTTP_200_OK)


class PagarEnEfectivo(APIView):
    """
    POST /api/pagos/efectivo/<id_de_la_orden>/
    Genera un código de pago para que el usuario pague en el punto elegido.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, id_de_la_orden):
        try:
            orden_a_pagar = Orden.objects.get(
                id=id_de_la_orden,
                comprador=request.user
            )
        except Orden.DoesNotExist:
            return Response(
                {'error': 'La orden no existe o no te pertenece'},
                status=status.HTTP_404_NOT_FOUND
            )

        if orden_a_pagar.estado != 'pendiente':
            return Response(
                {'error': f'Esta orden ya fue procesada — estado actual: {orden_a_pagar.estado}'},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializador_de_efectivo = SerializadorParaPagarEnEfectivo(data=request.data)
        if not serializador_de_efectivo.is_valid():
            return Response(
                serializador_de_efectivo.errors,
                status=status.HTTP_400_BAD_REQUEST
            )

        punto_elegido   = serializador_de_efectivo.validated_data['punto_de_pago']
        codigo_generado = generar_codigo_de_pago()

        pago_registrado = Pago.objects.create(
            orden_pagada     = orden_a_pagar,
            metodo_utilizado = 'efectivo',
            monto_cobrado_gs = orden_a_pagar.total_en_gs,
            estado_del_pago  = 'pendiente',
            codigo_de_pago   = codigo_generado,
            observacion_del_admin = f'Punto de pago: {punto_elegido}'
        )

        return Response({
            'mensaje':        f'Acercate a {punto_elegido.replace("_", " ").title()} y presentá este código',
            'codigo_de_pago': codigo_generado,
            'monto_a_pagar':  f'Gs. {orden_a_pagar.total_en_gs:,}',
            'pago':           SerializadorDePago(pago_registrado).data
        }, status=status.HTTP_200_OK)


class VerificarPagoDeTransferencia(APIView):
    """
    PUT /api/pagos/<id_del_pago>/verificar/
    El admin confirma o rechaza un pago por transferencia.
    """
    permission_classes = [IsAuthenticated]

    def put(self, request, id_del_pago):
        if not request.user.is_admin:
            return Response(
                {'error': 'Solo los administradores pueden verificar pagos'},
                status=status.HTTP_403_FORBIDDEN
            )

        try:
            pago_a_verificar = Pago.objects.get(id=id_del_pago)
        except Pago.DoesNotExist:
            return Response(
                {'error': 'El pago no existe'},
                status=status.HTTP_404_NOT_FOUND
            )

        decision_del_admin = request.data.get('decision')

        if decision_del_admin not in ['aprobar', 'rechazar']:
            return Response(
                {'error': 'La decisión debe ser "aprobar" o "rechazar"'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if decision_del_admin == 'aprobar':
            pago_a_verificar.estado_del_pago  = 'aprobado'
            pago_a_verificar.codigo_de_pago   = generar_codigo_de_pago()
            pago_a_verificar.orden_pagada.estado = 'pagada'
            pago_a_verificar.orden_pagada.save()
        else:
            pago_a_verificar.estado_del_pago = 'rechazado'

        pago_a_verificar.observacion_del_admin = request.data.get(
            'observacion', pago_a_verificar.observacion_del_admin
        )
        pago_a_verificar.save()

        return Response({
            'mensaje': f'Pago {pago_a_verificar.estado_del_pago} correctamente',
            'pago':    SerializadorDePago(pago_a_verificar).data
        })
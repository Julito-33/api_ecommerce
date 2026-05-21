from rest_framework import serializers
from .models import Pago


class SerializadorDePago(serializers.ModelSerializer):
    """
    Muestra el detalle completo de un pago.
    Se usa para confirmar el pago al usuario y en el panel admin.
    """
    numero_de_orden  = serializers.IntegerField(source='orden_pagada.id', read_only=True)
    nombre_del_comprador = serializers.CharField(source='orden_pagada.comprador.full_name', read_only=True)

    class Meta:
        model  = Pago
        fields = [
            'id', 'numero_de_orden', 'nombre_del_comprador',
            'metodo_utilizado', 'monto_cobrado_gs', 'estado_del_pago',
            'codigo_de_pago', 'ultimos_4_digitos',
            'observacion_del_admin', 'fecha_del_pago'
        ]


class SerializadorParaPagarConTarjeta(serializers.Serializer):
    """
    Valida los datos del formulario de tarjeta.
    Nunca guardamos el número completo — solo los últimos 4 dígitos.
    """
    numero_de_tarjeta    = serializers.CharField(min_length=16, max_length=16)
    nombre_en_la_tarjeta = serializers.CharField(max_length=100)
    mes_de_vencimiento   = serializers.IntegerField(min_value=1, max_value=12)
    anio_de_vencimiento  = serializers.IntegerField(min_value=2024, max_value=2035)
    codigo_cvv           = serializers.CharField(min_length=3, max_length=4)

    def validate_numero_de_tarjeta(self, numero_ingresado):
        # Verificamos que el número tenga solo dígitos
        if not numero_ingresado.isdigit():
            raise serializers.ValidationError('El número de tarjeta solo puede contener dígitos')
        return numero_ingresado


class SerializadorParaPagarConTransferencia(serializers.Serializer):
    """
    Valida los datos de una transferencia bancaria.
    El comprobante es obligatorio para verificar el pago.
    """
    banco_de_origen      = serializers.CharField(max_length=100)
    numero_de_referencia = serializers.CharField(max_length=50)
    comprobante          = serializers.ImageField()


class SerializadorParaPagarEnEfectivo(serializers.Serializer):
    """
    Para pago en efectivo solo necesitamos el punto de pago elegido.
    """
    punto_de_pago = serializers.ChoiceField(choices=[
        ('farmacia_catedral', 'Farmacia Catedral'),
        ('ande',              'ANDE'),
        ('copaco',            'COPACO'),
        ('seven_eleven',      'Seven Eleven'),
    ])
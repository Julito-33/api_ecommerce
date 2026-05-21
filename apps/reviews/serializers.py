from rest_framework import serializers
from .models import Resena


class SerializadorDeResena(serializers.ModelSerializer):
    nombre_del_autor     = serializers.CharField(source='autor_de_la_resena.full_name', read_only=True)
    nombre_del_producto  = serializers.CharField(source='producto_reseñado.nombre', read_only=True)

    class Meta:
        model  = Resena
        fields = [
            'id', 'nombre_del_autor', 'nombre_del_producto',
            'calificacion', 'titulo_de_la_resena', 'cuerpo_de_la_resena',
            'estado_de_moderacion', 'escrita_en'
        ]
        read_only_fields = ['id', 'estado_de_moderacion', 'escrita_en']


class SerializadorParaEscribirResena(serializers.ModelSerializer):
    """
    Solo recibe los campos que el usuario puede completar.
    El producto y el autor se asignan automáticamente en la vista.
    """

    class Meta:
        model  = Resena
        fields = ['calificacion', 'titulo_de_la_resena', 'cuerpo_de_la_resena']

    def validate_calificacion(self, puntaje_ingresado):
        if puntaje_ingresado < 1 or puntaje_ingresado > 5:
            raise serializers.ValidationError('La calificación debe estar entre 1 y 5 estrellas')
        return puntaje_ingresado
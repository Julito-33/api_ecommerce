# ─────────────────────────────────────────────────────────────────────────────
# apps/users/serializers.py
#
# Los serializers convierten los modelos de Django a JSON y viceversa.
# También validan los datos que llegan del frontend antes de guardarlos.
# ─────────────────────────────────────────────────────────────────────────────

from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from .models import User


class RegisterSerializer(serializers.ModelSerializer):
    """
    Serializer para registrar un usuario nuevo.
    Valida que la contraseña cumpla los requisitos de seguridad
    y que ambas contraseñas coincidan.
    """

    # write_only=True significa que este campo se recibe pero nunca
    # se devuelve en la respuesta — por seguridad
    password  = serializers.CharField(write_only=True, validators=[validate_password])
    password2 = serializers.CharField(write_only=True)

    class Meta:
        model  = User
        fields = ['email', 'first_name', 'last_name', 'phone', 'password', 'password2']

    def validate(self, data):
        # Verificar que las dos contraseñas coincidan
        if data['password'] != data['password2']:
            raise serializers.ValidationError({'password': 'Las contraseñas no coinciden'})
        return data

    def create(self, validated_data):
        # Eliminamos password2 porque el modelo no lo necesita
        validated_data.pop('password2')
        # create_user se encarga de hashear la contraseña automáticamente
        return User.objects.create_user(**validated_data)


class UserSerializer(serializers.ModelSerializer):
    """
    Serializer para mostrar los datos del usuario autenticado.
    Nunca expone la contraseña.
    """

    full_name = serializers.ReadOnlyField()

    class Meta:
        model  = User
        fields = [
            'id', 'email', 'first_name', 'last_name',
            'full_name', 'phone', 'role', 'created_at'
        ]
        # Estos campos solo se pueden leer, no modificar directamente
        read_only_fields = ['id', 'role', 'created_at']


class UpdateProfileSerializer(serializers.ModelSerializer):
    """
    Serializer para que el usuario actualice su perfil.
    Solo puede cambiar nombre, apellido y teléfono.
    No puede cambiar su email ni su rol.
    """

    class Meta:
        model  = User
        fields = ['first_name', 'last_name', 'phone']
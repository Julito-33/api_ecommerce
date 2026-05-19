# ─────────────────────────────────────────────────────────────────────────────
# apps/users/views.py
#
# Las vistas manejan cada endpoint de usuarios:
# - Registro
# - Ver y actualizar perfil
#
# El login y refresh de tokens los maneja simplejwt automáticamente,
# no necesitamos escribir esa lógica nosotros.
# ─────────────────────────────────────────────────────────────────────────────

from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny

from .serializers import RegisterSerializer, UserSerializer, UpdateProfileSerializer


class RegisterView(APIView):
    """
    POST /api/users/register/
    Endpoint público — cualquiera puede registrarse sin token.
    """

    # AllowAny sobreescribe la configuración global que pide autenticación
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)

        if serializer.is_valid():
            user = serializer.save()
            # Devolvemos los datos del usuario recién creado
            return Response(
                UserSerializer(user).data,
                status=status.HTTP_201_CREATED
            )

        # Si hay errores de validación, los devolvemos con 400
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ProfileView(APIView):
    """
    GET  /api/users/profile/  — ver perfil del usuario autenticado
    PUT  /api/users/profile/  — actualizar perfil
    """

    # Este endpoint sí requiere token JWT
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # request.user viene del token JWT, Django lo resuelve automáticamente
        serializer = UserSerializer(request.user)
        return Response(serializer.data)

    def put(self, request):
        serializer = UpdateProfileSerializer(
            request.user,
            data=request.data,
            # partial=True permite actualizar solo algunos campos
            partial=True
        )

        if serializer.is_valid():
            serializer.save()
            # Devolvemos el perfil completo actualizado
            return Response(UserSerializer(request.user).data)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.shortcuts import get_object_or_404

from apps.products.models import Producto
from .models import Resena
from .serializers import SerializadorDeResena, SerializadorParaEscribirResena


class ResenasDeUnProducto(APIView):
    """
    GET /api/resenas/<slug_del_producto>/
    Devuelve todas las reseñas aprobadas de un producto.
    Público — cualquiera puede leerlas sin token.
    """
    permission_classes = [AllowAny]

    def get(self, request, slug_del_producto):
        producto_consultado = get_object_or_404(Producto, slug=slug_del_producto)

        resenas_aprobadas = Resena.objects.filter(
            producto_reseñado=producto_consultado,
            estado_de_moderacion='aprobada'
        ).select_related('autor_de_la_resena')

        # Calculamos el promedio de calificaciones
        total_de_resenas    = resenas_aprobadas.count()
        promedio_de_estrellas = 0

        if total_de_resenas > 0:
            suma_de_calificaciones = sum(r.calificacion for r in resenas_aprobadas)
            promedio_de_estrellas  = round(suma_de_calificaciones / total_de_resenas, 1)

        serializador = SerializadorDeResena(resenas_aprobadas, many=True)

        return Response({
            'producto':             producto_consultado.nombre,
            'total_de_resenas':     total_de_resenas,
            'promedio_de_estrellas': promedio_de_estrellas,
            'resenas':              serializador.data
        })


class EscribirResena(APIView):
    """
    POST /api/resenas/<slug_del_producto>/escribir/
    El usuario autenticado escribe una reseña sobre un producto.
    La reseña queda en estado 'pendiente' hasta que el admin la apruebe.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, slug_del_producto):
        producto_a_reseñar = get_object_or_404(Producto, slug=slug_del_producto)

        # Verificar que el usuario no haya reseñado este producto antes
        resena_existente = Resena.objects.filter(
            producto_reseñado=producto_a_reseñar,
            autor_de_la_resena=request.user
        ).exists()

        if resena_existente:
            return Response(
                {'error': 'Ya escribiste una reseña para este producto'},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializador = SerializadorParaEscribirResena(data=request.data)

        if serializador.is_valid():
            resena_nueva = serializador.save(
                producto_reseñado  = producto_a_reseñar,
                autor_de_la_resena = request.user,
                estado_de_moderacion = 'pendiente'
            )
            return Response(
                {
                    'mensaje': 'Tu reseña fue enviada y está pendiente de aprobación',
                    'resena':  SerializadorDeResena(resena_nueva).data
                },
                status=status.HTTP_201_CREATED
            )

        return Response(serializador.errors, status=status.HTTP_400_BAD_REQUEST)


class ModerarResena(APIView):
    """
    PUT /api/resenas/<id_de_la_resena>/moderar/
    El admin aprueba o rechaza una reseña pendiente.
    """
    permission_classes = [IsAuthenticated]

    def put(self, request, id_de_la_resena):
        if not request.user.is_admin:
            return Response(
                {'error': 'Solo los administradores pueden moderar reseñas'},
                status=status.HTTP_403_FORBIDDEN
            )

        resena_a_moderar = get_object_or_404(Resena, id=id_de_la_resena)
        decision_del_admin = request.data.get('estado_de_moderacion')

        if decision_del_admin not in ['aprobada', 'rechazada']:
            return Response(
                {'error': 'El estado debe ser "aprobada" o "rechazada"'},
                status=status.HTTP_400_BAD_REQUEST
            )

        resena_a_moderar.estado_de_moderacion = decision_del_admin
        resena_a_moderar.save()

        return Response({
            'mensaje': f'Reseña {decision_del_admin} correctamente',
            'resena':  SerializadorDeResena(resena_a_moderar).data
        })


class ReseñasPendientes(APIView):
    """
    GET /api/resenas/pendientes/
    Lista todas las reseñas que esperan moderación.
    Solo administradores.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if not request.user.is_admin:
            return Response(
                {'error': 'Solo los administradores pueden ver las reseñas pendientes'},
                status=status.HTTP_403_FORBIDDEN
            )

        resenas_sin_revisar = Resena.objects.filter(
            estado_de_moderacion='pendiente'
        ).select_related('producto_reseñado', 'autor_de_la_resena')

        serializador = SerializadorDeResena(resenas_sin_revisar, many=True)
        return Response({
            'total_pendientes': resenas_sin_revisar.count(),
            'resenas':          serializador.data
        })
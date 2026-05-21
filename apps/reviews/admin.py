from django.contrib import admin
from .models import Resena


@admin.register(Resena)
class PanelDeResenas(admin.ModelAdmin):
    list_display  = ['producto_reseñado', 'autor_de_la_resena', 'calificacion', 'estado_de_moderacion', 'escrita_en']
    list_filter   = ['estado_de_moderacion', 'calificacion']
    search_fields = ['producto_reseñado__nombre', 'autor_de_la_resena__email']

    # Acción rápida para aprobar varias reseñas de una vez
    actions = ['aprobar_resenas_seleccionadas', 'rechazar_resenas_seleccionadas']

    def aprobar_resenas_seleccionadas(self, peticion_del_admin, resenas_elegidas):
        cantidad = resenas_elegidas.update(estado_de_moderacion='aprobada')
        self.message_user(peticion_del_admin, f'{cantidad} reseñas aprobadas correctamente')

    def rechazar_resenas_seleccionadas(self, peticion_del_admin, resenas_elegidas):
        cantidad = resenas_elegidas.update(estado_de_moderacion='rechazada')
        self.message_user(peticion_del_admin, f'{cantidad} reseñas rechazadas correctamente')

    aprobar_resenas_seleccionadas.short_description  = 'Aprobar reseñas seleccionadas'
    rechazar_resenas_seleccionadas.short_description = 'Rechazar reseñas seleccionadas'
from django.contrib import admin
from .models import Orden, ItemDeOrden


class ProductosDentroDeLaOrden(admin.TabularInline):
    model  = ItemDeOrden
    extra  = 0  # Sin formularios vacíos — los items vienen del carrito
    fields = ['variante_comprada', 'cantidad', 'precio_unitario_en_gs', 'subtotal_en_gs']
    readonly_fields = ['variante_comprada', 'cantidad', 'precio_unitario_en_gs', 'subtotal_en_gs']


@admin.register(Orden)
class PanelDeOrdenes(admin.ModelAdmin):
    list_display  = ['id', 'comprador', 'estado', 'metodo_de_pago', 'total_en_gs', 'creada_en']
    list_filter   = ['estado', 'metodo_de_pago']
    search_fields = ['comprador__email', 'comprador__first_name']
    readonly_fields = ['comprador', 'total_en_gs', 'creada_en']
    inlines       = [ProductosDentroDeLaOrden]

    # Acción rápida para marcar órdenes como enviadas desde la lista
    actions = ['marcar_como_enviadas']

    def marcar_como_enviadas(self, peticion_del_admin, ordenes_seleccionadas):
        cantidad_actualizada = ordenes_seleccionadas.update(estado='enviada')
        self.message_user(peticion_del_admin, f'{cantidad_actualizada} órdenes marcadas como enviadas')

    marcar_como_enviadas.short_description = 'Marcar órdenes seleccionadas como enviadas'
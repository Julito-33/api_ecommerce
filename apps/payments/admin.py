from django.contrib import admin
from .models import Pago


@admin.register(Pago)
class PanelDePagos(admin.ModelAdmin):
    list_display  = ['id', 'orden_pagada', 'metodo_utilizado', 'monto_cobrado_gs', 'estado_del_pago', 'fecha_del_pago']
    list_filter   = ['estado_del_pago', 'metodo_utilizado']
    search_fields = ['orden_pagada__id', 'codigo_de_pago']
    readonly_fields = ['codigo_de_pago', 'fecha_del_pago']

    actions = ['aprobar_pagos_seleccionados']

    def aprobar_pagos_seleccionados(self, peticion_del_admin, pagos_elegidos):
        for pago_a_aprobar in pagos_elegidos:
            pago_a_aprobar.estado_del_pago = 'aprobado'
            pago_a_aprobar.orden_pagada.estado = 'pagada'
            pago_a_aprobar.orden_pagada.save()
            pago_a_aprobar.save()
        self.message_user(peticion_del_admin, f'{pagos_elegidos.count()} pagos aprobados correctamente')

    aprobar_pagos_seleccionados.short_description = 'Aprobar pagos seleccionados'
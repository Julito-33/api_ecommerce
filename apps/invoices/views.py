import io
from django.http import FileResponse
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT

from apps.orders.models import Orden
from apps.payments.models import Pago

AZUL_EMPRESA  = colors.HexColor('#1e3a8a')
AZUL_MEDIO    = colors.HexColor('#2563eb')
AZUL_CLARO    = colors.HexColor('#dbeafe')
GRIS_OSCURO   = colors.HexColor('#1f2937')
GRIS_MEDIO    = colors.HexColor('#6b7280')
BLANCO        = colors.white

ANCHO_UTIL = A4[0] - 3.6*cm


def formato_guaranies(monto):
    return 'Gs. ' + '{:,}'.format(monto).replace(',', '.')


def p(texto, fs=9, color=None, bold=False, align=TA_LEFT):
    return Paragraph(texto, ParagraphStyle('_',
        fontSize=fs,
        textColor=color or GRIS_OSCURO,
        fontName='Helvetica-Bold' if bold else 'Helvetica',
        leading=fs + 3,
        alignment=align,
    ))


def construir_factura_en_pdf(orden_de_la_factura, pago_de_la_orden):
    buffer_del_pdf = io.BytesIO()

    documento_pdf = SimpleDocTemplate(
        buffer_del_pdf,
        pagesize=A4,
        rightMargin=1.8*cm,
        leftMargin=1.8*cm,
        topMargin=1.5*cm,
        bottomMargin=1.8*cm,
    )

    elementos = []

    # ── ENCABEZADO ────────────────────────────────────────────────────────────
    encabezado = Table([[
        p('TechStore Paraguay', fs=20, color=AZUL_EMPRESA, bold=True),
        p('+595 981 123 456\ncontacto@techstore.com.py\nAv. Mariscal Lopez 1234, Asunción\nRUC: 80012345-1',
          fs=8, color=GRIS_MEDIO, align=TA_RIGHT),
    ]], colWidths=[ANCHO_UTIL * 0.55, ANCHO_UTIL * 0.45])
    encabezado.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('TOPPADDING', (0,0), (-1,-1), 0),
        ('BOTTOMPADDING', (0,0), (-1,-1), 0),
    ]))
    elementos.append(encabezado)
    elementos.append(Spacer(1, 0.3*cm))
    elementos.append(HRFlowable(width='100%', thickness=3,
                                color=AZUL_EMPRESA, spaceAfter=8))

    # ── NÚMERO DE FACTURA ─────────────────────────────────────────────────────
    nro_factura = Table([[
        p(f'FACTURA N° {orden_de_la_factura.id:04d}',
          fs=16, color=AZUL_EMPRESA, bold=True),
        p(f'Fecha: {orden_de_la_factura.creada_en.strftime("%d/%m/%Y %H:%M")}',
          fs=9, color=GRIS_MEDIO, align=TA_RIGHT),
    ]], colWidths=[ANCHO_UTIL * 0.6, ANCHO_UTIL * 0.4])
    nro_factura.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
    ]))
    elementos.append(nro_factura)
    elementos.append(HRFlowable(width='100%', thickness=0.5,
                                color=colors.HexColor('#e2e8f0'), spaceAfter=10))

    # ── DATOS DEL CLIENTE ─────────────────────────────────────────────────────
    seccion_cliente = Table([[
        p('DATOS DEL CLIENTE', fs=8.5, color=BLANCO, bold=True),
    ]], colWidths=[ANCHO_UTIL])
    seccion_cliente.setStyle(TableStyle([
        ('BACKGROUND',    (0,0), (-1,-1), AZUL_EMPRESA),
        ('TOPPADDING',    (0,0), (-1,-1), 5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 5),
        ('LEFTPADDING',   (0,0), (-1,-1), 8),
    ]))
    elementos.append(seccion_cliente)
    elementos.append(Spacer(1, 0.1*cm))

    datos_cliente = Table([
        [p('Nombre:', bold=True, color=GRIS_MEDIO),
         p(orden_de_la_factura.comprador.full_name),
         p('Email:', bold=True, color=GRIS_MEDIO),
         p(orden_de_la_factura.comprador.email)],
        [p('Teléfono:', bold=True, color=GRIS_MEDIO),
         p(orden_de_la_factura.telefono_de_envio),
         p('Ciudad:', bold=True, color=GRIS_MEDIO),
         p(orden_de_la_factura.ciudad_de_envio)],
        [p('Dirección:', bold=True, color=GRIS_MEDIO),
         p(orden_de_la_factura.direccion_de_envio),
         p(''), p('')],
    ], colWidths=[2.5*cm, 7*cm, 2.5*cm, 5.5*cm])
    datos_cliente.setStyle(TableStyle([
        ('TOPPADDING',    (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ('LEFTPADDING',   (0,0), (-1,-1), 6),
        ('LINEBELOW',     (0,0), (-1,-2), 0.3, colors.HexColor('#e2e8f0')),
        ('BACKGROUND',    (0,0), (-1,-1), GRIS_CLARO if False else BLANCO),
        ('ROWBACKGROUNDS',(0,0), (-1,-1), [BLANCO, colors.HexColor('#f8fafc')]),
    ]))
    elementos.append(datos_cliente)
    elementos.append(Spacer(1, 0.3*cm))

    # ── DATOS DEL PAGO ────────────────────────────────────────────────────────
    seccion_pago = Table([[
        p('DATOS DEL PAGO', fs=8.5, color=BLANCO, bold=True),
    ]], colWidths=[ANCHO_UTIL])
    seccion_pago.setStyle(TableStyle([
        ('BACKGROUND',    (0,0), (-1,-1), AZUL_MEDIO),
        ('TOPPADDING',    (0,0), (-1,-1), 5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 5),
        ('LEFTPADDING',   (0,0), (-1,-1), 8),
    ]))
    elementos.append(seccion_pago)
    elementos.append(Spacer(1, 0.1*cm))

    datos_pago = Table([
        [p('Código de pago:', bold=True, color=GRIS_MEDIO),
         p(pago_de_la_orden.codigo_de_pago),
         p('Método:', bold=True, color=GRIS_MEDIO),
         p(orden_de_la_factura.get_metodo_de_pago_display())],
        [p('Estado:', bold=True, color=GRIS_MEDIO),
         p('✓ Pagado', color=colors.HexColor('#16a34a'), bold=True),
         p(''), p('')],
    ], colWidths=[3*cm, 6.5*cm, 2.5*cm, 5.5*cm])
    datos_pago.setStyle(TableStyle([
        ('TOPPADDING',    (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ('LEFTPADDING',   (0,0), (-1,-1), 6),
        ('LINEBELOW',     (0,0), (-1,-2), 0.3, colors.HexColor('#e2e8f0')),
        ('ROWBACKGROUNDS',(0,0), (-1,-1), [BLANCO, colors.HexColor('#f8fafc')]),
    ]))
    elementos.append(datos_pago)
    elementos.append(Spacer(1, 0.4*cm))

    # ── DETALLE DE PRODUCTOS ──────────────────────────────────────────────────
    seccion_detalle = Table([[
        p('DETALLE DE LA COMPRA', fs=8.5, color=BLANCO, bold=True),
    ]], colWidths=[ANCHO_UTIL])
    seccion_detalle.setStyle(TableStyle([
        ('BACKGROUND',    (0,0), (-1,-1), AZUL_EMPRESA),
        ('TOPPADDING',    (0,0), (-1,-1), 5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 5),
        ('LEFTPADDING',   (0,0), (-1,-1), 8),
    ]))
    elementos.append(seccion_detalle)
    elementos.append(Spacer(1, 0.1*cm))

    filas = [[
        p('Producto', bold=True, color=AZUL_EMPRESA),
        p('Talla', bold=True, color=AZUL_EMPRESA, align=TA_CENTER),
        p('Color', bold=True, color=AZUL_EMPRESA, align=TA_CENTER),
        p('Cant.', bold=True, color=AZUL_EMPRESA, align=TA_CENTER),
        p('Precio unit.', bold=True, color=AZUL_EMPRESA, align=TA_RIGHT),
        p('Subtotal', bold=True, color=AZUL_EMPRESA, align=TA_RIGHT),
    ]]

    for item in orden_de_la_factura.items_de_la_orden.all():
        filas.append([
            p(item.variante_comprada.producto_padre.nombre),
            p(item.variante_comprada.talla or '—', align=TA_CENTER),
            p(item.variante_comprada.color or '—', align=TA_CENTER),
            p(str(item.cantidad), align=TA_CENTER),
            p(formato_guaranies(item.precio_unitario_en_gs), align=TA_RIGHT),
            p(formato_guaranies(item.subtotal_en_gs), bold=True, align=TA_RIGHT),
        ])

    tabla_productos = Table(filas,
        colWidths=[7*cm, 1.8*cm, 2*cm, 1.5*cm, 3*cm, 2.2*cm])
    tabla_productos.setStyle(TableStyle([
        ('LINEBELOW',     (0,0), (-1,0),  1.2, AZUL_EMPRESA),
        ('ROWBACKGROUNDS',(0,1), (-1,-1), [BLANCO, AZUL_CLARO]),
        ('LINEBELOW',     (0,1), (-1,-1), 0.3, colors.HexColor('#e2e8f0')),
        ('TOPPADDING',    (0,0), (-1,-1), 5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 5),
        ('LEFTPADDING',   (0,0), (-1,-1), 5),
        ('RIGHTPADDING',  (0,0), (-1,-1), 5),
        ('VALIGN',        (0,0), (-1,-1), 'MIDDLE'),
        ('BOX',           (0,0), (-1,-1), 0.5, colors.HexColor('#cbd5e1')),
    ]))
    elementos.append(tabla_productos)
    elementos.append(Spacer(1, 0.4*cm))

    # ── TOTAL ─────────────────────────────────────────────────────────────────
    total_tabla = Table([[
        p(f'Total de items: {sum(i.cantidad for i in orden_de_la_factura.items_de_la_orden.all())}',
          fs=9, color=GRIS_MEDIO),
        p('TOTAL A PAGAR:', fs=11, color=GRIS_OSCURO, bold=True, align=TA_RIGHT),
        p(formato_guaranies(orden_de_la_factura.total_en_gs),
          fs=14, color=AZUL_EMPRESA, bold=True, align=TA_RIGHT),
    ]], colWidths=[ANCHO_UTIL * 0.35, ANCHO_UTIL * 0.38, ANCHO_UTIL * 0.27])
    total_tabla.setStyle(TableStyle([
        ('VALIGN',        (0,0), (-1,-1), 'MIDDLE'),
        ('BACKGROUND',    (1,0), (-1,-1), AZUL_CLARO),
        ('LINEABOVE',     (1,0), (-1,-1), 2, AZUL_EMPRESA),
        ('TOPPADDING',    (0,0), (-1,-1), 8),
        ('BOTTOMPADDING', (0,0), (-1,-1), 8),
        ('LEFTPADDING',   (0,0), (-1,-1), 6),
        ('RIGHTPADDING',  (0,0), (-1,-1), 8),
    ]))
    elementos.append(total_tabla)
    elementos.append(Spacer(1, 0.6*cm))

    # ── PIE ───────────────────────────────────────────────────────────────────
    elementos.append(HRFlowable(width='100%', thickness=0.5,
                                color=colors.HexColor('#e2e8f0'), spaceAfter=6))
    elementos.append(p(
        'Gracias por tu compra en TechStore Paraguay 🖥️  |  '
        'Este documento es comprobante válido de tu compra.',
        fs=8, color=GRIS_MEDIO, align=TA_CENTER
    ))

    documento_pdf.build(elementos)
    buffer_del_pdf.seek(0)
    return buffer_del_pdf


class DescargarFacturaPDF(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, id_de_la_orden):
        try:
            if request.user.is_admin:
                orden_solicitada = Orden.objects.get(id=id_de_la_orden)
            else:
                orden_solicitada = Orden.objects.get(
                    id=id_de_la_orden,
                    comprador=request.user
                )
        except Orden.DoesNotExist:
            return Response(
                {'error': 'La orden no existe o no te pertenece'},
                status=status.HTTP_404_NOT_FOUND
            )

        if orden_solicitada.estado not in ['pagada', 'preparando', 'enviada', 'entregada']:
            return Response(
                {'error': 'Solo se puede generar factura de órdenes pagadas'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            pago_aprobado = orden_solicitada.pago_de_la_orden
        except Pago.DoesNotExist:
            return Response(
                {'error': 'No se encontró un pago aprobado para esta orden'},
                status=status.HTTP_404_NOT_FOUND
            )

        pdf_generado       = construir_factura_en_pdf(orden_solicitada, pago_aprobado)
        nombre_del_archivo = f'factura_techstore_{id_de_la_orden:04d}.pdf'

        return FileResponse(
            pdf_generado,
            as_attachment=True,
            filename=nombre_del_archivo,
            content_type='application/pdf'
        )
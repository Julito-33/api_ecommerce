import io
from django.http import FileResponse
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_RIGHT

from apps.orders.models import Orden
from apps.payments.models import Pago


def formato_guaranies(monto):
    # Convierte 150000 → Gs. 150.000
    return 'Gs. ' + '{:,}'.format(monto).replace(',', '.')


def construir_factura_en_pdf(orden_de_la_factura, pago_de_la_orden):
    buffer_del_pdf = io.BytesIO()

    documento_pdf = SimpleDocTemplate(
        buffer_del_pdf,
        pagesize=A4,
        rightMargin=2*cm,
        leftMargin=2*cm,
        topMargin=2*cm,
        bottomMargin=2*cm
    )

    estilos_de_texto = getSampleStyleSheet()

    estilo_del_titulo = ParagraphStyle(
        'titulo_factura',
        parent=estilos_de_texto['Title'],
        fontSize=24,
        textColor=colors.HexColor('#FF6B00'),
        alignment=TA_CENTER,
        spaceAfter=10
    )

    elementos_del_pdf = []

    elementos_del_pdf.append(Paragraph('Tienda Naranja', estilo_del_titulo))
    elementos_del_pdf.append(Paragraph('tiendanaranja.com.py', estilos_de_texto['Normal']))
    elementos_del_pdf.append(Spacer(1, 0.5*cm))

    datos_de_la_factura = [
        ['FACTURA',        f'#{orden_de_la_factura.id:04d}'],
        ['Fecha',          orden_de_la_factura.creada_en.strftime('%d/%m/%Y %H:%M')],
        ['Cliente',        orden_de_la_factura.comprador.full_name],
        ['Email',          orden_de_la_factura.comprador.email],
        ['Código de pago', pago_de_la_orden.codigo_de_pago],
    ]

    tabla_de_encabezado = Table(datos_de_la_factura, colWidths=[4*cm, 12*cm])
    tabla_de_encabezado.setStyle(TableStyle([
        ('FONTNAME',      (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE',      (0, 0), (-1, -1), 10),
        ('TEXTCOLOR',     (0, 0), (0, -1), colors.HexColor('#FF6B00')),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))

    elementos_del_pdf.append(tabla_de_encabezado)
    elementos_del_pdf.append(Spacer(1, 0.5*cm))

    elementos_del_pdf.append(Paragraph('Datos de envío', estilos_de_texto['Heading2']))

    datos_de_envio = [
        ['Dirección', orden_de_la_factura.direccion_de_envio],
        ['Ciudad',    orden_de_la_factura.ciudad_de_envio],
        ['Teléfono',  orden_de_la_factura.telefono_de_envio],
    ]

    tabla_de_envio = Table(datos_de_envio, colWidths=[4*cm, 12*cm])
    tabla_de_envio.setStyle(TableStyle([
        ('FONTNAME',      (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE',      (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))

    elementos_del_pdf.append(tabla_de_envio)
    elementos_del_pdf.append(Spacer(1, 0.5*cm))

    elementos_del_pdf.append(Paragraph('Detalle de la compra', estilos_de_texto['Heading2']))

    filas_de_productos = [['Producto', 'Talla', 'Color', 'Cant.', 'Precio unit.', 'Subtotal']]

    for item_comprado in orden_de_la_factura.items_de_la_orden.all():
        filas_de_productos.append([
            item_comprado.variante_comprada.producto_padre.nombre,
            item_comprado.variante_comprada.talla,
            item_comprado.variante_comprada.color,
            str(item_comprado.cantidad),
            formato_guaranies(item_comprado.precio_unitario_en_gs),
            formato_guaranies(item_comprado.subtotal_en_gs),
        ])

    filas_de_productos.append([
        '', '', '', '', 'TOTAL',
        formato_guaranies(orden_de_la_factura.total_en_gs)
    ])

    tabla_de_productos = Table(
        filas_de_productos,
        colWidths=[5*cm, 2*cm, 2.5*cm, 1.5*cm, 3*cm, 3*cm]
    )

    tabla_de_productos.setStyle(TableStyle([
        ('BACKGROUND',     (0, 0), (-1, 0),  colors.HexColor('#FF6B00')),
        ('TEXTCOLOR',      (0, 0), (-1, 0),  colors.white),
        ('FONTNAME',       (0, 0), (-1, 0),  'Helvetica-Bold'),
        ('FONTSIZE',       (0, 0), (-1, -1), 9),
        ('ALIGN',          (3, 0), (-1, -1), 'RIGHT'),
        ('ROWBACKGROUNDS', (0, 1), (-1, -2), [colors.white, colors.HexColor('#FFF3E0')]),
        ('GRID',           (0, 0), (-1, -2), 0.5, colors.grey),
        ('FONTNAME',       (0, -1), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE',       (0, -1), (-1, -1), 11),
        ('TEXTCOLOR',      (-1, -1), (-1, -1), colors.HexColor('#FF6B00')),
        ('LINEABOVE',      (0, -1), (-1, -1), 1.5, colors.HexColor('#FF6B00')),
    ]))

    elementos_del_pdf.append(tabla_de_productos)
    elementos_del_pdf.append(Spacer(1, 1*cm))

    elementos_del_pdf.append(Paragraph(
        'Gracias por tu compra — Tienda Naranja',
        estilos_de_texto['Normal']
    ))

    documento_pdf.build(elementos_del_pdf)
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
        nombre_del_archivo = f'factura_tienda_naranja_{id_de_la_orden:04d}.pdf'

        return FileResponse(
            pdf_generado,
            as_attachment=True,
            filename=nombre_del_archivo,
            content_type='application/pdf'
        )
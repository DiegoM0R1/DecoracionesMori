from django.shortcuts import render, get_object_or_404
from django.views.generic import ListView, DetailView
from .models import Service, ServiceCategory
from django.views.generic import TemplateView

from django.http import JsonResponse
from django.contrib.admin.views.decorators import staff_member_required
from .models import Product, Service

@staff_member_required
def get_product_data(request, product_id):
    try:
        product = Product.objects.get(pk=product_id)
        return JsonResponse({
            'id': product.id,
            'name': product.name,
            'price_per_unit': str(product.price_per_unit),
            'unit': product.unit,
            # Agrega campo stock si lo implementaste
        })
    except Product.DoesNotExist:
        return JsonResponse({'error': 'Producto no encontrado'}, status=404)

@staff_member_required
def get_service_data(request, service_id):
    try:
        service = Service.objects.get(pk=service_id)
        return JsonResponse({
            'id': service.id,
            'name': service.name,
            'base_price': str(service.base_price),
        })
    except Service.DoesNotExist:
        return JsonResponse({'error': 'Servicio no encontrado'}, status=404)

def product_api(request, product_id):
    try:
        product = Product.objects.get(id=product_id)
        return JsonResponse({
            'id': product.id,
            'name': product.name,
            'price_per_unit': float(product.price_per_unit),
            'unit': product.unit
        })
    except Product.DoesNotExist:
        return JsonResponse({'error': 'Producto no encontrado'}, status=404)

def service_api(request, service_id):
    try:
        service = Service.objects.get(id=service_id)
        return JsonResponse({
            'id': service.id,
            'name': service.name,
            'base_price': float(service.base_price)
        })
    except Service.DoesNotExist:
        return JsonResponse({'error': 'Servicio no encontrado'}, status=404)
class HomeView(TemplateView):
    template_name = 'home.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Obtener todas las categorías y un servicio de cada una
        categories = ServiceCategory.objects.all()
        categories_with_service = []
        for category in categories:
            service = Service.objects.filter(category=category, is_active=True).first()
            if service:
                categories_with_service.append({
                    'category': category,
                    'service': service
                })
        context['categories_with_service'] = categories_with_service
        return context
class ServiceListView(ListView):
    model = Service
    context_object_name = 'services'
    template_name = 'services/service_list.html'
    
    def get_queryset(self):
        queryset = super().get_queryset().filter(is_active=True)
        category_id = self.kwargs.get('id')
        if category_id:
            queryset = queryset.filter(category__id=category_id)
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = ServiceCategory.objects.all()
        context['categoria_actual'] = None
        category_id = self.kwargs.get('id')
        if category_id:
            context['categoria_actual'] = get_object_or_404(ServiceCategory, id=category_id)
        return context

class ServiceDetailView(DetailView):
    model = Service
    context_object_name = 'service'
    template_name = 'services/service_detail.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['imagenes'] = self.object.images.all()
        context['videos'] = self.object.videos.all()
        context['servicios_relacionados'] = Service.objects.filter(category=self.object.category).exclude(id=self.object.id)[:5]
        # Añadir los componentes (productos) asociados al servicio
        context['componentes'] = self.object.components.all().select_related('product')
        # Añadir contexto para el modal de login si no está autenticado
        if not self.request.user.is_authenticated:
            context['show_login_modal'] = True
        return context
    

from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse, JsonResponse
from django.contrib.auth.decorators import login_required
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import inch
import datetime
import io
from decimal import Decimal
import json

def vista_cotizacion(request, service_id):
    """Vista interactiva para cotización tipo chatbot"""
    service = get_object_or_404(Service, pk=service_id)
    componentes = service.components.all().select_related('product')
    
    # Preparar datos para JSON
    service_data = {
        'id': service.id,
        'name': service.name,
        'basePrice': float(service.base_price) if service.base_price else 0
    }
    
    componentes_data = []
    for comp in componentes:
        # Determinar URL de imagen
        image_url = '/static/imagen/default-product.jpg'
        featured_image = comp.product.get_featured_image()
        if featured_image:
            if featured_image.image:
                image_url = featured_image.image.url
        
        # Añadir datos del componente
        componentes_data.append({
            'id': comp.product.id,
            'name': comp.product.name,
            'price': float(comp.product.price_per_unit) if comp.product.price_per_unit else 0,
            'unit': comp.product.unit or '',
            'quantity': float(comp.quantity) if comp.quantity else 0,
            'imageUrl': image_url
        })
    
    context = {
        'service': service,
        'componentes': componentes,
        'service_json': json.dumps(service_data),
        'componentes_json': json.dumps(componentes_data)
    }
    return render(request, 'services/cotizacion_interactiva.html', context)

@login_required
def generar_pdf_cotizacion(request, service_id):
    """Genera PDF basado en selecciones del usuario - VERSIÓN COMPLETAMENTE DINÁMICA"""
    service = get_object_or_404(Service, pk=service_id)
    
    # Obtener datos de la solicitud POST
    selecciones = json.loads(request.POST.get('selecciones', '{}'))
    # Ya no necesitamos metros_totales como campo obligatorio
    
    # Crear buffer para el PDF
    buffer = io.BytesIO()
    
    # Crear documento
    doc = SimpleDocTemplate(buffer, pagesize=letter, 
                           rightMargin=72, leftMargin=72,
                           topMargin=72, bottomMargin=72)
    
    # Contenedor para elementos
    elements = []
    
    # Estilos
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name='Centered', alignment=1))
    
    # Información de la cotización
    elements.append(Paragraph("Decoraciones Mori", styles['Heading1']))
    elements.append(Paragraph("Cotización Personalizada", styles['Heading2']))
    elements.append(Spacer(1, 12))
    
    # Número de cotización
    num_cotizacion = f"COT-{service_id}-{datetime.datetime.now().strftime('%Y%m%d%H%M')}"
    elements.append(Paragraph(f"<b>Cotización Nº:</b> {num_cotizacion}", styles['Normal']))
    elements.append(Paragraph(f"<b>Fecha:</b> {datetime.datetime.now().strftime('%d/%m/%Y')}", styles['Normal']))
    elements.append(Paragraph(f"<b>Válido hasta:</b> {(datetime.datetime.now() + datetime.timedelta(days=15)).strftime('%d/%m/%Y')}", styles['Normal']))
    elements.append(Spacer(1, 12))
    
    # Información del cliente
    elements.append(Paragraph("INFORMACIÓN DEL CLIENTE", styles['Heading3']))
    elements.append(Paragraph(f"<b>Nombre:</b> {request.user.get_full_name() or request.user.username}", styles['Normal']))
    elements.append(Paragraph(f"<b>Email:</b> {request.user.email}", styles['Normal']))
    elements.append(Spacer(1, 24))
    
    # Detalles del servicio
    elements.append(Paragraph("DETALLE DEL SERVICIO SOLICITADO", styles['Heading3']))
    elements.append(Spacer(1, 12))
    
    # Servicio base
    service_data = [
        ["Servicio", "Precio Base Referencial"],
        [service.name, f"S/. {service.base_price}" if service.base_price else "Consultar"]
    ]
    
    service_table = Table(service_data, colWidths=[4*inch, 1.5*inch])
    service_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (1, 0), colors.lightgrey),
        ('TEXTCOLOR', (0, 0), (1, 0), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.white),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    
    elements.append(service_table)
    elements.append(Spacer(1, 20))
    
    # Productos seleccionados
    if selecciones:
        elements.append(Paragraph("PRODUCTOS SELECCIONADOS", styles['Heading3']))
        elements.append(Spacer(1, 12))
        
        product_data = [
            ["Producto", "Cantidad", "Unidad", "Precio Unit.", "Subtotal"]
        ]
        
        subtotal = Decimal('0.00')
        
        # Añadir productos seleccionados
        for producto_id, cantidad in selecciones.items():
            try:
                producto_id = int(producto_id)
                cantidad = Decimal(str(cantidad))
                
                # Obtener el componente relacionado
                componente = service.components.filter(product_id=producto_id).first()
                if componente and cantidad > 0:
                    precio_unitario = componente.product.price_per_unit
                    producto_subtotal = precio_unitario * cantidad
                    subtotal += producto_subtotal
                    
                    # Formatear cantidad según el tipo de unidad
                    cantidad_formateada = format_quantity_for_pdf(cantidad, componente.product.unit)
                    
                    product_data.append([
                        componente.product.name,
                        cantidad_formateada,
                        componente.product.unit,
                        f"S/. {precio_unitario:.2f}",
                        f"S/. {producto_subtotal:.2f}"
                    ])
            except (ValueError, TypeError):
                continue
        
        if len(product_data) > 1:  # Si hay productos seleccionados
            prod_table = Table(product_data, colWidths=[2.2*inch, 0.8*inch, 0.8*inch, 1*inch, 1*inch])
            prod_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.white),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ]))
            
            elements.append(prod_table)
            elements.append(Spacer(1, 20))
            
            # Calcular totales
            igv = subtotal * Decimal('0.18')
            total = subtotal + igv
            
            # Tabla de totales
            totales_data = [
                ["", ""],
                ["Subtotal:", f"S/. {subtotal:.2f}"],
                ["IGV (18%):", f"S/. {igv:.2f}"],
                ["", ""],
                ["TOTAL:", f"S/. {total:.2f}"]
            ]
            
            totales_table = Table(totales_data, colWidths=[3*inch, 1.5*inch])
            totales_table.setStyle(TableStyle([
                ('ALIGN', (0, 0), (-1, -1), 'RIGHT'),
                ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
                ('FONTNAME', (0, 1), (-1, 3), 'Helvetica'),
                ('FONTSIZE', (0, -1), (-1, -1), 14),
                ('LINEABOVE', (0, -1), (-1, -1), 2, colors.black),
                ('LINEBELOW', (0, -1), (-1, -1), 2, colors.black),
                ('BACKGROUND', (0, -1), (-1, -1), colors.lightgrey),
            ]))
            
            elements.append(totales_table)
        else:
            elements.append(Paragraph("No se seleccionaron productos específicos.", styles['Normal']))
    else:
        elements.append(Paragraph("Esta cotización se basa en el servicio base. Los productos específicos se definirán en la evaluación técnica.", styles['Normal']))
    
    elements.append(Spacer(1, 30))
    
    # Notas importantes
    elements.append(Paragraph("INFORMACIÓN IMPORTANTE", styles['Heading3']))
    
    notas = [
        "Esta cotización se basa en las cantidades específicas que usted seleccionó para cada producto.",
        "El precio final puede variar según la evaluación técnica realizada en sitio.",
        "Esta cotización es válida por 15 días calendario desde la fecha de emisión.",
        "Los precios mostrados incluyen IGV (18%).",
        "Para proceder con el servicio, es necesaria una evaluación técnica previa.",
        "Cualquier modificación en cantidades o especificaciones puede alterar el precio final."
    ]
    
    for i, nota in enumerate(notas, 1):
        elements.append(Paragraph(f"{i}. {nota}", styles['Normal']))
        elements.append(Spacer(1, 6))
    
    elements.append(Spacer(1, 20))
    
    # Información de contacto
    elements.append(Paragraph("CONTACTO", styles['Heading3']))
    elements.append(Paragraph("<b>Teléfono:</b> +51 999 999 999", styles['Normal']))
    elements.append(Paragraph("<b>Email:</b> info@decoracionesmori.com", styles['Normal']))
    elements.append(Paragraph("<b>Horario de atención:</b> Lunes a Viernes de 8:00 AM a 6:00 PM", styles['Normal']))
    
    # Construir PDF
    doc.build(elements)
    
    # Valor del buffer de archivo
    pdf = buffer.getvalue()
    buffer.close()
    
    # Crear respuesta HTTP
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'inline; filename="cotizacion_{service.name.replace(" ", "_")}_{datetime.datetime.now().strftime("%Y%m%d")}.pdf"'
    response.write(pdf)
    
    return response

def format_quantity_for_pdf(cantidad, unit):
    """Formatea la cantidad para mostrar en el PDF según el tipo de unidad"""
    unit_lower = unit.lower().strip()
    
    # Unidades discretas - mostrar como entero si es posible
    discrete_units = [
        'pieza', 'piezas', 'unidad', 'unidades', 'und',
        'paño', 'paños', 'panel', 'paneles',
        'rollo', 'rollos', 'bobina', 'bobinas',
        'galón', 'galones', 'galon', 'galones',
        'lata', 'latas', 'balde', 'baldes',
        'saco', 'sacos', 'bolsa', 'bolsas',
        'caja', 'cajas', 'paquete', 'paquetes'
    ]
    
    is_discrete = any(discrete in unit_lower for discrete in discrete_units)
    
    if is_discrete:
        # Para unidades discretas, mostrar como entero si no tiene decimales significativos
        if cantidad % 1 == 0:
            return str(int(cantidad))
        else:
            return f"{cantidad:.1f}"
    else:
        # Para unidades continuas, mostrar con hasta 2 decimales, removiendo ceros innecesarios
        return f"{cantidad:.2f}".rstrip('0').rstrip('.')

# Vista auxiliar para obtener información del servicio (útil para AJAX)
def get_service_components(request, service_id):
    """API endpoint para obtener componentes de un servicio"""
    if not request.user.is_staff:
        return JsonResponse({'error': 'No autorizado'}, status=403)
    
    try:
        service = Service.objects.get(pk=service_id)
        components = []
        
        for component in service.components.all():
            featured_image = component.product.get_featured_image()
            image_url = '/static/imagen/default-product.jpg'
            
            if featured_image and featured_image.image:
                image_url = featured_image.image.url
            
            components.append({
                'id': component.product.id,
                'name': component.product.name,
                'price': float(component.product.price_per_unit),
                'unit': component.product.unit,
                'imageUrl': image_url,
                'defaultQuantity': float(component.quantity)
            })
        
        return JsonResponse({
            'service': {
                'id': service.id,
                'name': service.name,
                'basePrice': float(service.base_price) if service.base_price else 0
            },
            'components': components
        })
    
    except Service.DoesNotExist:
        return JsonResponse({'error': 'Servicio no encontrado'}, status=404)
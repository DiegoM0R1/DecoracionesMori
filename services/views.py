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
    """Genera PDF basado en selecciones del usuario"""
    service = get_object_or_404(Service, pk=service_id)
    
    # Obtener datos de la solicitud POST
    selecciones = json.loads(request.POST.get('selecciones', '{}'))
    metros_totales = Decimal(request.POST.get('metros_totales', '0'))
    
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
    elements.append(Paragraph(f"Cotización Nº: {num_cotizacion}", styles['Normal']))
    elements.append(Paragraph(f"Fecha: {datetime.datetime.now().strftime('%d/%m/%Y')}", styles['Normal']))
    elements.append(Paragraph(f"Válido hasta: {(datetime.datetime.now() + datetime.timedelta(days=15)).strftime('%d/%m/%Y')}", styles['Normal']))
    elements.append(Spacer(1, 12))
    
    # Información del cliente
    elements.append(Paragraph("Información del Cliente:", styles['Heading3']))
    elements.append(Paragraph(f"Nombre: {request.user.get_full_name() or request.user.username}", styles['Normal']))
    elements.append(Paragraph(f"Email: {request.user.email}", styles['Normal']))
    elements.append(Spacer(1, 24))
    
    # Detalles del servicio
    elements.append(Paragraph("Detalle de su cotización personalizada:", styles['Heading3']))
    elements.append(Spacer(1, 12))
    
    # Servicio base
    service_data = [
        ["Servicio Base", "Precio Referencial"],
        [service.name, f"S/. {service.base_price}"]
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
    
    # Área total
    elements.append(Spacer(1, 12))
    elements.append(Paragraph(f"Área total: {metros_totales} m²", styles['Normal']))
    elements.append(Spacer(1, 12))
    
    # Productos seleccionados
    product_data = [
        ["Producto", "Cantidad", "Precio Unit.", "Subtotal"]
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
                
                product_data.append([
                    componente.product.name,
                    f"{cantidad} {componente.product.unit}",
                    f"S/. {precio_unitario}",
                    f"S/. {producto_subtotal}"
                ])
        except (ValueError, TypeError):
            continue
    
    if len(product_data) > 1:  # Si hay productos seleccionados
        elements.append(Paragraph("Productos seleccionados:", styles['Heading3']))
        elements.append(Spacer(1, 12))
        
        prod_table = Table(product_data, colWidths=[2*inch, 1.2*inch, 1.2*inch, 1.2*inch])
        prod_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        elements.append(prod_table)
    
    # Calcular totales
    igv = subtotal * Decimal('0.18')
    total = subtotal + igv
    
    elements.append(Spacer(1, 24))
    
    # Tabla de totales
    totales_data = [
        ["Subtotal:", f"S/. {subtotal:.2f}"],
        ["IGV (18%):", f"S/. {igv:.2f}"],
        ["TOTAL:", f"S/. {total:.2f}"]
    ]
    
    totales_table = Table(totales_data, colWidths=[2*inch, 1.5*inch])
    totales_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (0, -1), 'LEFT'),
        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
        ('LINEABOVE', (0, -1), (-1, -1), 1, colors.black),
        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
    ]))
    
    elements.append(totales_table)
    
    # Notas sobre precio estimado
    elements.append(Spacer(1, 24))
    elements.append(Paragraph("IMPORTANTE:", styles['Heading4']))
    elements.append(Paragraph("Esta es una cotización de referencia basada en sus selecciones. El precio final puede variar según la evaluación técnica en sitio.", 
                             styles['Normal']))
    
    # Notas al pie
    elements.append(Spacer(1, 24))
    elements.append(Paragraph("Notas:", styles['Heading4']))
    elements.append(Paragraph("1. Esta cotización es válida por 15 días calendario.", styles['Normal']))
    elements.append(Paragraph("2. Los precios incluyen IGV.", styles['Normal']))
    elements.append(Paragraph("3. Para consultas adicionales, contáctenos al: +51 999 999 999", styles['Normal']))
    elements.append(Paragraph("4. Correo electrónico: info@decoracionesmori.com", styles['Normal']))
    
    # Construir PDF
    doc.build(elements)
    
    # Valor del buffer de archivo
    pdf = buffer.getvalue()
    buffer.close()
    
    # Crear respuesta HTTP
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'inline; filename="cotizacion_personalizada_{service.name.replace(" ", "_")}_{datetime.datetime.now().strftime("%Y%m%d")}.pdf"'
    response.write(pdf)
    
    return response
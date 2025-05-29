# inventory/admin_views.py
from django.contrib import admin # Necesario para admin.site.each_context
from django.contrib.admin.views.decorators import staff_member_required
from django.utils.translation import gettext_lazy as _
from django.db.models import F, Sum # Count, Q no se usan en el código actual que pasaste
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.core.serializers.json import DjangoJSONEncoder
from datetime import datetime

from .models import InventoryStatus, InventoryMovement
from services.models import Product, ProductCategory # Asegúrate que estas importaciones sean correctas

@staff_member_required
def inventory_report(request):
    """Vista para generar un reporte completo de inventario."""
    categories = ProductCategory.objects.all()
    category_id = request.GET.get('category')
    status_filter = request.GET.get('status')
    
    queryset = InventoryStatus.objects.select_related(
        'product', 'product__category'
    ).order_by('product__category__name', 'product__name')
    
    if category_id:
        queryset = queryset.filter(product__category_id=category_id)
    if status_filter == 'low':
        queryset = queryset.filter(current_stock__lt=F('product__stock_min'))
    elif status_filter == 'out':
        queryset = queryset.filter(current_stock__lte=0)
    
    stats = {
        'total_products': queryset.count(),
        'low_stock': queryset.filter(current_stock__lt=F('product__stock_min')).count(),
        'out_of_stock': queryset.filter(current_stock__lte=0).count(),
    }
    
    category_summary = []
    for category in categories:
        category_items = queryset.filter(product__category=category)
        if category_items.exists():
            category_summary.append({
                'category': category,
                'product_count': category_items.count(),
                'low_stock': category_items.filter(current_stock__lt=F('product__stock_min')).count(),
            })
            
    recent_movements = InventoryMovement.objects.filter(
        draft=False
    ).select_related('product').order_by('-created_at')[:10]
    
    products_without_status = Product.objects.exclude(
        id__in=InventoryStatus.objects.values_list('product_id', flat=True)
    )
    
    # Bandera para saber si se crearon nuevos estados y necesitamos re-filtrar
    refilter_needed = False
    if products_without_status.exists():
        refilter_needed = True # Marcar que se crearon estados
        for product in products_without_status:
            entradas = InventoryMovement.objects.filter(
                product=product, movement_type='entrada', draft=False
            ).aggregate(total=Sum('quantity'))['total'] or 0
            salidas = InventoryMovement.objects.filter(
                product=product, movement_type='salida', draft=False
            ).aggregate(total=Sum('quantity'))['total'] or 0
            stock_actual = entradas - salidas
            InventoryStatus.objects.create(product=product, current_stock=stock_actual)
        
        # Si se crearon nuevos estados, volvemos a obtener el queryset completo
        queryset = InventoryStatus.objects.select_related(
            'product', 'product__category'
        ).order_by('product__category__name', 'product__name')
        # Y re-aplicamos filtros
        if category_id:
            queryset = queryset.filter(product__category_id=category_id)
        if status_filter == 'low':
            queryset = queryset.filter(current_stock__lt=F('product__stock_min'))
        elif status_filter == 'out':
            queryset = queryset.filter(current_stock__lte=0)
        # Actualizar también las stats si el queryset cambió
        stats = {
            'total_products': queryset.count(),
            'low_stock': queryset.filter(current_stock__lt=F('product__stock_min')).count(),
            'out_of_stock': queryset.filter(current_stock__lte=0).count(),
        }


    context = {
        'title': _('Reporte de Inventario'),
        'inventory_items': queryset,
        'categories': categories,
        'selected_category': category_id,
        'selected_status': status_filter,
        'stats': stats,
        'category_summary': category_summary,
        'recent_movements': recent_movements,
        'opts': InventoryStatus._meta, # Para la plantilla del admin
        'app_label': InventoryStatus._meta.app_label, # Para la plantilla del admin
        'has_change_permission': request.user.has_perm('inventory.change_inventorystatus'),
    }
    context.update(admin.site.each_context(request)) # MUY IMPORTANTE para plantillas de admin
    return render(request, 'admin/inventory/inventory_report.html', context)

@staff_member_required
def product_history(request, product_id):
    """Vista para mostrar el historial de movimientos de un producto (Kardex)."""
    product = get_object_or_404(Product, pk=product_id)
    
    # Asegurar que InventoryStatus exista y esté actualizado
    entradas_total = InventoryMovement.objects.filter(
        product=product, movement_type='entrada', draft=False
    ).aggregate(total=Sum('quantity'))['total'] or 0
    salidas_total = InventoryMovement.objects.filter(
        product=product, movement_type='salida', draft=False
    ).aggregate(total=Sum('quantity'))['total'] or 0
    current_stock_calculated = entradas_total - salidas_total

    inventory_status, created = InventoryStatus.objects.get_or_create(
        product=product,
        defaults={'current_stock': current_stock_calculated}
    )
    if not created and inventory_status.current_stock != current_stock_calculated:
        inventory_status.current_stock = current_stock_calculated
        inventory_status.save(update_fields=['current_stock'])
        
    # Historial de movimientos confirmados para mostrar en orden cronológico (el más antiguo primero)
    confirmed_movements = InventoryMovement.objects.filter(
        product=product, draft=False
    ).order_by('created_at') # Ordenar por más antiguo primero para calcular saldo cronológico

    movement_history_display = []
    balance = 0  # El saldo inicial antes de cualquier movimiento registrado es 0
                 # O podrías buscar el primer movimiento y calcular el saldo inicial antes de ese.
                 # Para un kardex, usualmente se parte de 0 y se reconstruye.

    for movement in confirmed_movements:
        if movement.movement_type == 'entrada':
            balance += movement.quantity
        else: # salida
            balance -= movement.quantity
        movement_history_display.append({
            'movement': movement,
            'balance': balance 
        })

    context = {
        'title': _('Historial de Producto: {}').format(product.name),
        'product': product,
        'movement_history': movement_history_display, # Ya está en orden cronológico
        'current_balance': inventory_status.current_stock, # El stock actual definitivo
        'opts': Product._meta, # O InventoryMovement._meta, según lo que represente mejor la página
        'app_label': Product._meta.app_label,
        'has_change_permission': request.user.has_perm('inventory.change_inventorymovement'),
    }
    context.update(admin.site.each_context(request)) # MUY IMPORTANTE
    return render(request, 'admin/inventory/product_history.html', context)

# --- NUEVA API PARA EL CALENDARIO DE MOVIMIENTOS ---
@staff_member_required
def inventory_movement_events_api(request):
    start_str = request.GET.get('start')
    end_str = request.GET.get('end')
    product_filter = request.GET.get('product_id')

    if not start_str or not end_str:
        return JsonResponse({'error': 'Parámetros start y end son requeridos'}, status=400)

    try:
        start_date = datetime.fromisoformat(start_str.replace('Z', '+00:00')).date()
        end_date = datetime.fromisoformat(end_str.replace('Z', '+00:00')).date()
    except ValueError:
        return JsonResponse({'error': 'Formato de fecha inválido'}, status=400)

    movements_query = InventoryMovement.objects.filter(
        created_at__date__range=[start_date, end_date]
    ).select_related('product')

    if product_filter and product_filter != 'all':
        movements_query = movements_query.filter(product_id=product_filter)

    events = []
    for movement in movements_query:
        event_color = '#0d6efd' # Azul por defecto
        if movement.movement_type == 'entrada': event_color = '#198754' # Verde Bootstrap
        elif movement.movement_type == 'salida': event_color = '#dc3545' # Rojo Bootstrap
        if movement.draft: event_color = '#ffc107' # Amarillo Bootstrap

        title = f"{movement.product.name}: {movement.get_movement_type_display()} ({movement.quantity})"
        if movement.draft: title = f"[BORRADOR] {title}"

        events.append({
            'id': f'movement-{movement.id}',
            'title': title,
            'start': movement.created_at.isoformat(),
            'backgroundColor': event_color,
            'borderColor': event_color,
            'textColor': '#ffffff' if movement.movement_type != 'salida' and not movement.draft else ('#000000' if movement.draft else '#ffffff'),
            'extendedProps': {
                'movement_id': movement.id,
                'product_name': movement.product.name,
                'quantity': float(movement.quantity),
                'movement_type': movement.get_movement_type_display(),
                'movement_type_raw': movement.movement_type,
                'document_reference': movement.document_reference or "N/A",
                'notes': movement.notes or "Ninguna",
                'is_draft': movement.draft,
                'created_at_display': movement.created_at.strftime("%d/%m/%Y %H:%M")
            }
        })
    return JsonResponse(events, safe=False, encoder=DjangoJSONEncoder)

# inventory/admin_views.py
# ... (tus importaciones existentes) ...
from django.http import HttpResponse
from django.template.loader import render_to_string
# from weasyprint import HTML, CSS # Descomenta después de instalar WeasyPrint
# from django.conf import settings # Para buscar CSS estáticos
# import os # Para buscar CSS estáticos

# ... (tus vistas inventory_report, product_history, inventory_movement_events_api) ...

@staff_member_required
def export_inventory_report_pdf(request):
    # Obtener los mismos datos que inventory_report
    # (Esta lógica es similar a la de inventory_report, puedes refactorizarla en una función helper)
    categories = ProductCategory.objects.all()
    category_id = request.GET.get('category') # Para mantener los filtros
    status_filter = request.GET.get('status')

    queryset = InventoryStatus.objects.select_related(
        'product', 'product__category'
    ).order_by('product__category__name', 'product__name')

    if category_id:
        queryset = queryset.filter(product__category_id=category_id)
    if status_filter == 'low':
        queryset = queryset.filter(current_stock__lt=F('product__stock_min'))
    elif status_filter == 'out':
        queryset = queryset.filter(current_stock__lte=0)

    # No necesitas todas las stats complejas para el PDF, solo los items.
    # Pero puedes incluirlas si tu plantilla PDF las usa.
    context = {
        'inventory_items': queryset,
        'title': _('Reporte de Inventario (PDF)'),
        'categories': categories, # Si quieres mostrar un resumen o filtros aplicados
        'selected_category_name': ProductCategory.objects.get(id=category_id).name if category_id else None,
        'selected_status': status_filter,
        'report_date': datetime.now()
    }

    # Renderiza una plantilla HTML específica para el PDF
    # Esta plantilla debe ser simple y estar diseñada para la conversión a PDF
    html_string = render_to_string('admin/inventory/inventory_report_pdf_template.html', context)

    # --- Sección de WeasyPrint (descomenta y ajusta cuando lo tengas instalado) ---
    # try:
    #     html = HTML(string=html_string, base_url=request.build_absolute_uri())
    #
    #     # Puedes añadir CSS para el PDF
    #     # css_path = os.path.join(settings.STATIC_ROOT, 'css/report_pdf.css') # Ejemplo
    #     # if os.path.exists(css_path):
    #     #     pdf_stylesheet = CSS(css_path)
    #     #     pdf_bytes = html.write_pdf(stylesheets=[pdf_stylesheet])
    #     # else:
    #     #     pdf_bytes = html.write_pdf()
    #     pdf_bytes = html.write_pdf()
    #
    #     response = HttpResponse(pdf_bytes, content_type='application/pdf')
    #     response['Content-Disposition'] = f'attachment; filename="reporte_inventario_{datetime.now().strftime("%Y%m%d")}.pdf"'
    #     return response
    # except Exception as e:
    #     # Log del error e
    #     print(f"Error generando PDF: {e}")
    #     return HttpResponse(f"Error generando el PDF: {e}. Asegúrate que WeasyPrint y sus dependencias estén instalados.", status=500)
    # --- Fin Sección WeasyPrint ---

    # Placeholder si WeasyPrint no está configurado aún:
    return HttpResponse(f"La generación de PDF aún no está implementada. HTML del reporte para PDF:<br><hr>{html_string}", content_type="text/html")
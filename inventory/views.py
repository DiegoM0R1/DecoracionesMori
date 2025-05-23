from django.shortcuts import render, get_object_or_404
from django.contrib.admin.views.decorators import staff_member_required
from django.utils.translation import gettext_lazy as _
from django.db.models import F, Sum, Count, Q
from django.urls import reverse

from .models import InventoryStatus, InventoryMovement
from services.models import Product, ProductCategory

@staff_member_required
def inventory_report(request):
    """Vista para generar un reporte completo de inventario en el panel de administración"""
    categories = ProductCategory.objects.all()
    
    # Filtros
    category_id = request.GET.get('category')
    status_filter = request.GET.get('status')   
    
    # Obtener todos los productos con su estado de inventario
    queryset = InventoryStatus.objects.select_related(
        'product', 'product__category'
    ).order_by('product__category__name', 'product__name')
    
    # Aplicar filtros
    if category_id:
        queryset = queryset.filter(product__category_id=category_id)
    
    if status_filter == 'low':
        queryset = queryset.filter(current_stock__lt=F('product__stock_min'))
    elif status_filter == 'out':
        queryset = queryset.filter(current_stock__lte=0)
    
    # Estadísticas
    stats = {
        'total_products': queryset.count(),
        'low_stock': queryset.filter(current_stock__lt=F('product__stock_min')).count(),
        'out_of_stock': queryset.filter(current_stock__lte=0).count(),
    }
    
    # Resumen por categoría
    category_summary = []
    for category in categories:
        category_items = queryset.filter(product__category=category)
        if category_items.exists():
            category_summary.append({
                'category': category,
                'product_count': category_items.count(),
                'low_stock': category_items.filter(current_stock__lt=F('product__stock_min')).count(),
            })
    
    # Movimientos recientes (últimos 10)
    recent_movements = InventoryMovement.objects.filter(
        draft=False
    ).select_related('product').order_by('-created_at')[:10]
    
    # Verificar si hay productos sin estado de inventario
    products_without_status = Product.objects.exclude(
        id__in=InventoryStatus.objects.values_list('product_id', flat=True)
    )
    
    if products_without_status.exists():
        # Crear estados de inventario para productos que no los tienen
        for product in products_without_status:
            # Calcular movimientos
            entradas = InventoryMovement.objects.filter(
                product=product, 
                movement_type='entrada',
                draft=False
            ).aggregate(total=Sum('quantity'))['total'] or 0
            
            salidas = InventoryMovement.objects.filter(
                product=product,
                movement_type='salida',
                draft=False
            ).aggregate(total=Sum('quantity'))['total'] or 0
            
            stock_actual = entradas - salidas
            
            # Crear estado de inventario
            InventoryStatus.objects.create(
                product=product,
                current_stock=stock_actual
            )
        
        # Actualizar queryset para incluir los nuevos estados
        queryset = InventoryStatus.objects.select_related(
            'product', 'product__category'
        ).order_by('product__category__name', 'product__name')
    
    context = {
        'title': _('Reporte de Inventario'),
        'inventory_items': queryset,
        'categories': categories,
        'selected_category': category_id,
        'selected_status': status_filter,
        'stats': stats,
        'category_summary': category_summary,
        'recent_movements': recent_movements,
        # Agregar extras para el admin
        'opts': InventoryStatus._meta,
        'app_label': 'inventory',
        'has_change_permission': request.user.has_perm('inventory.change_inventorystatus'),
    }
    
    return render(request, 'admin/inventory/inventory_report.html', context)

@staff_member_required
def product_history(request, product_id):
    """Vista para mostrar el historial de movimientos de un producto"""
    product = get_object_or_404(Product, pk=product_id)
    
    # Movimientos del producto
    movements = InventoryMovement.objects.filter(
        product=product
    ).order_by('-created_at')
    
    # Calcular saldo en cada movimiento
    balance = 0
    movement_history = []
    
    for movement in movements:
        if movement.draft:
            continue  # Ignorar borradores
            
        if movement.movement_type == 'entrada':
            balance += movement.quantity
        else:
            balance -= movement.quantity
            
        movement_history.append({
            'movement': movement,
            'balance': balance
        })
    
    # Invertir para mostrar en orden cronológico
    movement_history.reverse()
    
    # Obtener el stock actual
    try:
        inventory_status = InventoryStatus.objects.get(product=product)
        current_balance = inventory_status.current_stock
    except InventoryStatus.DoesNotExist:
        # Si no existe, calcularlo y crearlo
        entradas = InventoryMovement.objects.filter(
            product=product, 
            movement_type='entrada',
            draft=False
        ).aggregate(total=Sum('quantity'))['total'] or 0
        
        salidas = InventoryMovement.objects.filter(
            product=product,
            movement_type='salida',
            draft=False
        ).aggregate(total=Sum('quantity'))['total'] or 0
        
        current_balance = entradas - salidas
        
        # Crear estado de inventario
        inventory_status = InventoryStatus.objects.create(
            product=product,
            current_stock=current_balance
        )
    
    context = {
        'title': _('Historial de Producto: {}').format(product.name),
        'product': product,
        'movement_history': movement_history,
        'current_balance': current_balance,
        # Agregar extras para el admin
        'opts': InventoryStatus._meta,
        'app_label': 'inventory',
        'has_change_permission': request.user.has_perm('inventory.change_inventorystatus'),
    }
    
    return render(request, 'admin/inventory/product_history.html', context)
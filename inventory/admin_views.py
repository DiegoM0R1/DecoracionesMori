# inventory/admin_views.py
from django.contrib import admin # Import the admin site
from django.contrib.admin.views.decorators import staff_member_required
from django.utils.translation import gettext_lazy as _
from django.db.models import F, Sum, Count, Q # Added Count, Q from a later version
from django.shortcuts import render, get_object_or_404
# from django.urls import reverse # Not used in this snippet directly but good for other uses

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
    
    # (Incorporating logic from the more complete version of inventory_report)
    # Verificar si hay productos sin estado de inventario
    products_without_status = Product.objects.exclude(
        id__in=InventoryStatus.objects.values_list('product_id', flat=True)
    )
    
    if products_without_status.exists():
        for product in products_without_status:
            entradas = InventoryMovement.objects.filter(
                product=product, movement_type='entrada', draft=False
            ).aggregate(total=Sum('quantity'))['total'] or 0
            salidas = InventoryMovement.objects.filter(
                product=product, movement_type='salida', draft=False
            ).aggregate(total=Sum('quantity'))['total'] or 0
            stock_actual = entradas - salidas
            InventoryStatus.objects.create(
                product=product, current_stock=stock_actual
            )
        # Re-fetch queryset if it was modified by new InventoryStatus entries
        queryset = InventoryStatus.objects.select_related(
            'product', 'product__category'
        ).order_by('product__category__name', 'product__name')
        # Re-apply filters if necessary, or adjust logic
        if category_id:
            queryset = queryset.filter(product__category_id=category_id)
        if status_filter == 'low':
            queryset = queryset.filter(current_stock__lt=F('product__stock_min'))
        elif status_filter == 'out':
            queryset = queryset.filter(current_stock__lte=0)


    context = {
        'title': _('Reporte de Inventario'),
        'inventory_items': queryset,
        'categories': categories,
        'selected_category': category_id,
        'selected_status': status_filter,
        'stats': stats,
        'category_summary': category_summary,
        'recent_movements': recent_movements,
        'opts': InventoryStatus._meta,
        'app_label': 'inventory',
        'has_change_permission': request.user.has_perm('inventory.change_inventorystatus'),
    }
    
    # --- IMPORTANT CHANGE ---
    # Explicitly add the admin site's context (includes 'available_apps')
    # Use admin.site unless you have a custom admin site instance you registered.
    # If you have a custom AdminSite instance (e.g., site = MyAdminSite()), use that.
    context.update(admin.site.each_context(request)) 
    # --- END IMPORTANT CHANGE ---
    
    return render(request, 'admin/inventory/inventory_report.html', context)

@staff_member_required
def product_history(request, product_id):
    """Vista para mostrar el historial de movimientos de un producto"""
    product = get_object_or_404(Product, pk=product_id)
    
    movements = InventoryMovement.objects.filter(
        product=product
    ).order_by('-created_at') # Order by most recent first for calculation
    
    # Calculate balance considering the order for history
    # This calculation seems to be for a running balance from oldest to newest.
    # If movements are fetched -created_at, you might want to reverse before iterating for chronological balance.
    # The provided code snippet later reverses 'movement_history', so fetching -created_at is fine.

    current_stock_calculated = 0
    # Calculate current stock from non-draft movements up to now
    entradas_total = InventoryMovement.objects.filter(
        product=product, movement_type='entrada', draft=False
    ).aggregate(total=Sum('quantity'))['total'] or 0
    salidas_total = InventoryMovement.objects.filter(
        product=product, movement_type='salida', draft=False
    ).aggregate(total=Sum('quantity'))['total'] or 0
    current_stock_calculated = entradas_total - salidas_total

    # Ensure InventoryStatus exists and is correct, or create/update it
    inventory_status, created = InventoryStatus.objects.get_or_create(
        product=product,
        defaults={'current_stock': current_stock_calculated}
    )
    if not created and inventory_status.current_stock != current_stock_calculated:
        inventory_status.current_stock = current_stock_calculated
        inventory_status.save()
    
    current_balance_from_status = inventory_status.current_stock

    # Prepare movement history with running balance (chronological)
    # To show history chronologically with correct running balance, iterate from oldest to newest
    # So, fetch normally or reverse the initially fetched `movements` if it was `-created_at`
    
    # Recalculate balance for history display (chronological)
    balance = 0 
    movement_history_display = []
    # Iterate from the oldest movement to the newest for chronological history
    for movement in reversed(list(movements.filter(draft=False))): # Process confirmed movements, oldest first
        if movement.movement_type == 'entrada':
            balance += movement.quantity
        else: # salida
            balance -= movement.quantity
        movement_history_display.append({
            'movement': movement,
            'balance': balance # This balance is at the time of THIS movement
        })
    # movement_history_display is now chronological with correct running balances.
    # The original code had a complex balance calculation. This ensures chronological balance.

    context = {
        'title': _('Historial de Producto: {}').format(product.name),
        'product': product,
        'movement_history': movement_history_display, # Use the chronologically ordered list
        'current_balance': current_balance_from_status, # Display the definitive current stock
        'opts': InventoryStatus._meta, # Or Product._meta if more relevant for product history page title
        'app_label': 'inventory',
        'has_change_permission': request.user.has_perm('inventory.change_inventorystatus'), # Or relevant product perm
    }

    # --- IMPORTANT CHANGE ---
    context.update(admin.site.each_context(request))
    # --- END IMPORTANT CHANGE ---
    
    return render(request, 'admin/inventory/product_history.html', context)
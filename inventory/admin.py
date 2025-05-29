# inventory/admin.py
from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from django.utils.html import format_html
from django.urls import path, reverse, NoReverseMatch
from django.shortcuts import redirect # No se usa directamente aquí, pero por si acaso

from .models import InventoryStatus, InventoryMovement # Importa los modelos primero
from services.models import Product # Para el filtro de productos
# Importa tus vistas de admin personalizadas DESPUÉS de los modelos y el bloque unregister
from .admin_views import inventory_report, product_history 

# --- BLOQUE PARA DES-REGISTRAR MODELOS (AÑADE ESTO AL INICIO) ---
# Esto ayuda a evitar errores 'AlreadyRegistered' con el reloader del servidor de desarrollo.
try:
    admin.site.unregister(InventoryStatus)
except admin.sites.NotRegistered:
    pass
try:
    admin.site.unregister(InventoryMovement)
except admin.sites.NotRegistered:
    pass
# --- FIN DEL BLOQUE UNREGISTER ---

# --- Admin para InventoryStatus ---
@admin.register(InventoryStatus) # Esta es la línea 13 (después de importaciones y unregister)
class InventoryStatusAdmin(admin.ModelAdmin):
    list_display = ('product_name', 'current_stock', 'stock_min', 'stock_status', 'last_updated', 'actions_buttons')
    list_filter = ('product__category__name', 'product__is_active') 
    search_fields = ('product__name', 'product__description')
    readonly_fields = ('current_stock', 'last_updated')
    actions = ['update_inventory_status_action'] 

    change_list_template = 'admin/inventory/inventorystatus/change_list.html'


    def get_urls(self):
        urls = super().get_urls()
        info = self.model._meta.app_label, self.model._meta.model_name
        custom_urls = [
            path('report/', self.admin_site.admin_view(inventory_report), name=f'{info[0]}_{info[1]}_view_report'),
            path('product/<int:product_id>/history/', self.admin_site.admin_view(product_history), name=f'{info[0]}_{info[1]}_product_kardex'),
        ]
        return custom_urls + urls

    def actions_buttons(self, obj):
        info = self.model._meta.app_label, self.model._meta.model_name
        history_url_name = f'admin:{info[0]}_{info[1]}_product_kardex'
        try:
            history_url = reverse(history_url_name, args=[obj.product.id])
        except NoReverseMatch:
            history_url = "#" 
        add_movement_url = reverse('admin:inventory_inventorymovement_add') + f'?product={obj.product.id}&movement_type=entrada'
        return format_html(
            '<a href="{}" class="button" title="Ver historial del producto" style="margin-right:5px;"><i class="fas fa-history"></i> Historial</a>'
            '<a href="{}" class="button" title="Registrar nueva entrada"><i class="fas fa-plus"></i> Entrada</a>',
            history_url, add_movement_url
        )
    actions_buttons.short_description = _('Acciones')

    def product_name(self, obj): return obj.product.name
    product_name.short_description = _('Producto')

    def stock_min(self, obj): return obj.product.stock_min
    stock_min.short_description = _('Stock Mínimo')

    def stock_status(self, obj):
        if hasattr(obj, 'is_below_minimum') and obj.is_below_minimum():
            return format_html('<span style="color: red; font-weight: bold;">⚠️ BAJO MÍNIMO</span>')
        elif obj.current_stock <= 0:
            return format_html('<span style="color: darkred; font-weight: bold;">🚫 SIN STOCK</span>')
        return format_html('<span style="color: green;">✓ Normal</span>')
    stock_status.short_description = _('Estado')
    
    def update_inventory_status_action(self, request, queryset): 
        updated_count = 0
        for item in queryset:
            if hasattr(item, 'update_stock'): 
                item.update_stock()
                updated_count += 1
        self.message_user(request, _('Se actualizaron {} registros de estado de inventario.').format(updated_count))
    update_inventory_status_action.short_description = _('Actualizar stock del estado seleccionado') 
    
    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        info = self.model._meta.app_label, self.model._meta.model_name
        report_url_name = f'admin:{info[0]}_{info[1]}_view_report'
        try:
            extra_context['report_button'] = {'url': reverse(report_url_name),'label': _('Ver Reporte General')}
        except NoReverseMatch:
            extra_context['report_button'] = {'url': '#', 'label': _('Error URL Reporte')}
        
        # Esto es crucial para que tus plantillas de admin personalizadas tengan el contexto base
        extra_context.update(admin.site.each_context(request))
        return super().changelist_view(request, extra_context=extra_context)

# --- Admin para InventoryMovement ---
@admin.register(InventoryMovement)
class InventoryMovementAdmin(admin.ModelAdmin):
    change_list_template = 'admin/inventory/movement_calendar.html' # Usamos el calendario
    list_display = ('product', 'quantity', 'movement_type', 'document_reference', 'draft_status', 'created_at')
    list_filter = ('movement_type', 'draft', 'product__category__name', 'created_at')
    search_fields = ('product__name', 'document_reference', 'notes')
    ordering = ('-created_at',)
    date_hierarchy = 'created_at'
    
    fieldsets = (
        (None, {'fields': ('product', 'quantity', 'movement_type', 'document_reference', 'invoice_item', 'notes', 'draft')}),
        (_('Información de Fecha'), {'fields': ('created_at',), 'classes': ('collapse',)}),
    )
    readonly_fields = ('created_at',)
    actions = ['confirm_movements_action', 'mark_as_draft_action']

    def draft_status(self, obj):
        return format_html('<span style="color: orange;">Borrador</span>') if obj.draft else format_html('<span style="color: green;">Confirmado</span>')
    draft_status.short_description = _('Estado')

    def confirm_movements_action(self, request, queryset):
        updated = 0
        product_ids_to_update = set()
        for movement in queryset.filter(draft=True):
            movement.draft = False
            movement.save(update_fields=['draft']) 
            product_ids_to_update.add(movement.product_id)
            updated +=1
            
        for product_id in product_ids_to_update:
            inventory_status, created = InventoryStatus.objects.get_or_create(product_id=product_id)
            if hasattr(inventory_status, 'update_stock'): 
                inventory_status.update_stock()
        self.message_user(request, _('Se confirmaron {} movimientos. Stock(s) afectado(s) actualizado(s).').format(updated))
    confirm_movements_action.short_description = _('Confirmar movimientos y actualizar stock')

    def mark_as_draft_action(self, request, queryset):
        updated = queryset.filter(draft=False).update(draft=True)
        self.message_user(request, _('Se marcaron {} movimientos como borrador.').format(updated))
    mark_as_draft_action.short_description = _('Marcar seleccionados como borrador')
    
    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        extra_context['title'] = _('Calendario de Movimientos de Inventario')
        try:
            extra_context['products_for_filter'] = Product.objects.filter(is_active=True).order_by('name')
        except Exception:
             extra_context['products_for_filter'] = []
        
        extra_context.update(admin.site.each_context(request)) # Crucial
        return super().changelist_view(request, extra_context=extra_context)

# ... (otro código como la configuración de verbose_name para la app si lo tienes)
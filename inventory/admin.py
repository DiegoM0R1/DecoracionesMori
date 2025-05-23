# inventory/admin.py
from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from django.utils.html import format_html
from django.urls import path, reverse
from django.shortcuts import redirect

from .admin_views import inventory_report, product_history
from .models import InventoryMovement, InventoryStatus
# from services.models import Product, ProductCategory # Ensure this is correctly imported

# --- Unregister models (optional, for development convenience) ---
try:
    admin.site.unregister(InventoryStatus)
except admin.sites.NotRegistered:
    pass
try:
    admin.site.unregister(InventoryMovement)
except admin.sites.NotRegistered:
    pass
# --- End Unregister ---
from .admin_views import inventory_report, product_history # Ensure this is correct
from django.urls import NoReverseMatch
@admin.register(InventoryStatus)
class InventoryStatusAdmin(admin.ModelAdmin):
    list_display = ('product_name', 'current_stock', 'stock_min', 'stock_status', 'last_updated', 'actions_buttons') # 'actions_buttons' is key here
    list_filter = ('product__category', 'product__is_active')
    search_fields = ('product__name', 'product__description')
    readonly_fields = ('current_stock', 'last_updated')
    
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('report/', self.admin_site.admin_view(inventory_report), name='view_report'),
            # This is the path for product history, named 'product_kardex'
            path('product/<int:product_id>/history/', self.admin_site.admin_view(product_history), name='product_kardex'),
        ]
        return custom_urls + urls
    
    def _get_admin_url_name(self, action_name_suffix):
        """Helper to construct the full admin URL name."""
        return f'{self.admin_site.name}:{self.model._meta.app_label}_{self.model._meta.model_name}_{action_name_suffix}'


    def actions_buttons(self, obj):
        # Construct the name for reversing: 'admin:inventory_inventorystatus_product_kardex'
        history_url_name_to_reverse = self._get_admin_url_name('product_kardex')
        
        print(f"Attempting to reverse for 'actions_buttons': '{history_url_name_to_reverse}' with args: [{obj.product.id}]") # DEBUG

        try:
                history_url = reverse(history_url_name_to_reverse, args=[obj.product.id])
        except NoReverseMatch as e:
                print(f"ERROR in actions_buttons: NoReverseMatch for '{history_url_name_to_reverse}' - {e}") # DEBUG
                history_url = "#error-reversing-history-url" # Fallback URL

        add_movement_url = reverse('admin:inventory_inventorymovement_add') + f'?product={obj.product.id}&movement_type=entrada'

        return format_html(
            '<a href="{}" class="button" style="background-color: #17a2b8; color: white;">'
            '<i class="fas fa-history"></i> Ver Historial</a> '
            '<a href="{}" class="button" style="background-color: #28a745; color: white;">'
            '<i class="fas fa-plus"></i> Registrar Entrada</a>',
            history_url,
            add_movement_url
        )
    actions_buttons.short_description = _('Acciones')

    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        report_url_name_for_context = self._get_admin_url_name('view_report') 
        try:
            extra_context['inventory_report_url_from_admin'] = reverse(report_url_name_for_context)
        except Exception as e:
            print(f"Error reversing '{report_url_name_for_context}' for template (changelist_view): {e}")
            extra_context['inventory_report_url_from_admin'] = '#' 
            
        return super().changelist_view(request, extra_context=extra_context)
    
    
    def product_name(self, obj):
        return obj.product.name
    product_name.short_description = _('Producto')
    
    def stock_min(self, obj):
        return obj.product.stock_min
    stock_min.short_description = _('Stock Mínimo')
    
    def stock_status(self, obj):
        if hasattr(obj, 'is_below_minimum') and obj.is_below_minimum():
            return format_html('<span style="color: red; font-weight: bold;">⚠️ BAJO MÍNIMO</span>')
        else:
            return format_html('<span style="color: green;">✓ Normal</span>')
    stock_status.short_description = _('Estado')
    

    
    def update_inventory_status(self, request, queryset):
        updated_count = 0
        for item in queryset:
            if hasattr(item, 'update_stock'):
                item.update_stock()
                updated_count += 1
        self.message_user(request, _('Se actualizaron {} registros de inventario.').format(updated_count))
    update_inventory_status.short_description = _('Actualizar inventario seleccionado')
    
    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        
        report_url_name = self._get_admin_url_name('view_report') # Use helper and new name
        print(f"Attempting to reverse for report button: '{report_url_name}'") # DEBUG PRINT
        
        try:
            extra_context['report_button'] = {
                'url': reverse(report_url_name),
                'label': _('Ver Reporte de Inventario')
            }
        except Exception as e:
            print(f"NoReverseMatch for '{report_url_name}': {e}") # DEBUG PRINT
            extra_context['report_button'] = { # Fallback or error display
                'url': '#error-generating-url',
                'label': _('Error al generar URL del reporte')
            }
            
        return super().changelist_view(request, extra_context=extra_context)

@admin.register(InventoryMovement)
class InventoryMovementAdmin(admin.ModelAdmin):
    # ... (list_display, list_filter, search_fields, ordering, fieldsets, readonly_fields, actions, draft_status, confirm_movements, mark_as_draft - KEEP AS IS)
    list_display = ('product', 'quantity', 'movement_type', 'document_reference', 'draft_status', 'created_at')
    list_filter = ('movement_type', 'draft', 'product__category')
    search_fields = ('product__name', 'document_reference', 'notes')
    ordering = ('-created_at',)
    
    fieldsets = (
        (None, {
            'fields': ('product', 'quantity', 'movement_type', 'document_reference', 'invoice_item', 'notes', 'draft')
        }),
        (_('Información de Fecha'), {
            'fields': ('created_at',),
            'classes': ('collapse',), 
        }),
    )
    readonly_fields = ('created_at',)
    actions = ['confirm_movements', 'mark_as_draft']

    def draft_status(self, obj):
        if obj.draft:
            return format_html('<span style="color: orange;">Borrador</span>')
        else:
            return format_html('<span style="color: green;">Confirmado</span>')
    draft_status.short_description = _('Estado')

    def confirm_movements(self, request, queryset):
        updated = queryset.filter(draft=True).update(draft=False)
        product_ids = queryset.values_list('product_id', flat=True).distinct()
        for product_id in product_ids:
            inventory, created = InventoryStatus.objects.get_or_create(product_id=product_id)
            if hasattr(inventory, 'update_stock'):
                inventory.update_stock()
        self.message_user(request, _('Se confirmaron {} movimientos de inventario.').format(updated))
    confirm_movements.short_description = _('Confirmar movimientos seleccionados')

    def mark_as_draft(self, request, queryset):
        updated = queryset.filter(draft=False).update(draft=True)
        product_ids = queryset.values_list('product_id', flat=True).distinct()
        for product_id in product_ids:
            inventory, created = InventoryStatus.objects.get_or_create(product_id=product_id)
            if hasattr(inventory, 'update_stock'):
                inventory.update_stock()
        self.message_user(request, _('Se marcaron {} movimientos como borrador.').format(updated))
    mark_as_draft.short_description = _('Marcar seleccionados como borrador')
    
    def changelist_view(self, request, extra_context=None):
        # Construct the target URL name using the helper from InventoryStatusAdmin (or replicate logic)
        # The target is 'view_report' under 'inventory_inventorystatus'
        target_report_url_name = f'{admin.site.name}:inventory_inventorystatus_view_report' # Explicitly build
        print(f"Attempting to reverse for redirect: '{target_report_url_name}'") # DEBUG PRINT

        try:
            report_url = reverse(target_report_url_name)
            return redirect(report_url)
        except Exception as e:
            print(f"NoReverseMatch for redirect target '{target_report_url_name}': {e}") # DEBUG PRINT
            # Fallback: display the default changelist or an error message
            # For simplicity, let's call super, but you might want a user-facing error.
            extra_context = extra_context or {}
            extra_context['admin_redirect_error'] = f"Error al redirigir al reporte: {target_report_url_name} no encontrado."
            return super().changelist_view(request, extra_context)

# ----- Verbose names (keep as is or manage in apps.py/models.py) -----
from django.apps import apps
try:
    app_config_inventory = apps.get_app_config('inventory')
    app_config_inventory.verbose_name = _("Inventario")
except LookupError:
    pass

InventoryStatus._meta.verbose_name = _("Estado de Inventario")
InventoryStatus._meta.verbose_name_plural = _("Estados de Inventario")
InventoryMovement._meta.verbose_name = _("Movimiento de Inventario")
InventoryMovement._meta.verbose_name_plural = _("Movimientos de Inventario")
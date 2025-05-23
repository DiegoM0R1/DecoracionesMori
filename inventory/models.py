# models.py
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.db.models import Sum
from services.models import Product

class InventoryStatus(models.Model):
    """Modelo para mantener el estado actual del inventario"""
    product = models.OneToOneField(Product, on_delete=models.CASCADE, related_name='inventory_status')
    current_stock = models.DecimalField(_('Stock Actual'), max_digits=10, decimal_places=2, default=0)
    last_updated = models.DateTimeField(_('Última Actualización'), auto_now=True)
    
    class Meta:
        verbose_name = _('Estado de Inventario')
        verbose_name_plural = _('Estados de Inventario')
    
    def __str__(self):
        return f"Inventario de {self.product.name}: {self.current_stock} {self.product.unit}"
    
    def is_below_minimum(self):
        """Verifica si el stock actual está por debajo del mínimo establecido"""
        return self.current_stock < self.product.stock_min
    
    def update_stock(self):
        """Actualiza el stock basado en los movimientos de inventario"""
        # Calcular entradas (excluyendo borradores)
        entradas = InventoryMovement.objects.filter(
            product=self.product,
            movement_type='entrada',
            draft=False
        ).aggregate(total=Sum('quantity'))['total'] or 0
        
        # Calcular salidas (excluyendo borradores)
        salidas = InventoryMovement.objects.filter(
            product=self.product,
            movement_type='salida',
            draft=False
        ).aggregate(total=Sum('quantity'))['total'] or 0
        
        # Actualizar stock
        self.current_stock = entradas - salidas
        self.save()
        
        return self.current_stock

# Actualizar el modelo existente para agregar el campo draft
class InventoryMovement(models.Model):
    MOVEMENT_TYPE_CHOICES = (
        ('entrada', _('Entrada')),
        ('salida', _('Salida')),
    )
    
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='movements')
    quantity = models.DecimalField(_('Cantidad'), max_digits=10, decimal_places=2)
    movement_type = models.CharField(_('Tipo de Movimiento'), max_length=10, choices=MOVEMENT_TYPE_CHOICES)
    document_reference = models.CharField(_('Documento de referencia'), max_length=20, blank=True, null=True)
    invoice_item = models.ForeignKey('invoices.InvoiceItem', on_delete=models.SET_NULL, null=True, blank=True)
    notes = models.TextField(_('Notas'), blank=True)
    created_at = models.DateTimeField(_('Fecha de registro'), auto_now_add=True)
    draft = models.BooleanField(_('Borrador'), default=False, 
                               help_text=_('Indica si este movimiento está en borrador y no debe afectar al inventario real'))
    
    class Meta:
        verbose_name = _('Movimiento de Inventario')
        verbose_name_plural = _('Movimientos de Inventario')
    
    def __str__(self):
        return f"{self.get_movement_type_display()} de {self.quantity} de {self.product.name}"


# admin.py
from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from django.utils.html import format_html
from django.urls import reverse

from .models import InventoryMovement, InventoryStatus

@admin.register(InventoryStatus)
class InventoryStatusAdmin(admin.ModelAdmin):
    list_display = ('product_name', 'current_stock', 'stock_min', 'stock_status', 'last_updated')
    list_filter = ('product__category', 'product__is_active')
    search_fields = ('product__name', 'product__description')
    readonly_fields = ('current_stock', 'last_updated')
    
    def product_name(self, obj):
        return obj.product.name
    product_name.short_description = _('Producto')
    
    def stock_min(self, obj):
        return obj.product.stock_min
    stock_min.short_description = _('Stock Mínimo')
    
    def stock_status(self, obj):
        if obj.is_below_minimum():
            return format_html('<span style="color: red; font-weight: bold;">⚠️ BAJO MÍNIMO</span>')
        else:
            return format_html('<span style="color: green;">✓ Normal</span>')
    stock_status.short_description = _('Estado')
    
    # Agrega acciones personalizadas
    actions = ['update_inventory_status']
    
    def update_inventory_status(self, request, queryset):
        updated = 0
        for inventory in queryset:
            inventory.update_stock()
            updated += 1
        
        self.message_user(request, _('Se actualizaron {} registros de inventario.').format(updated))
    update_inventory_status.short_description = _('Actualizar inventario seleccionado')

@admin.register(InventoryMovement)
class InventoryMovementAdmin(admin.ModelAdmin):
    list_display = ('product', 'quantity', 'movement_type', 'document_reference', 'draft_status', 'created_at')
    list_filter = ('movement_type', 'draft', 'product__category', 'created_at')
    search_fields = ('product__name', 'document_reference', 'notes')
    ordering = ('-created_at',)
    date_hierarchy = 'created_at'
    
    def draft_status(self, obj):
        if obj.draft:
            return format_html('<span style="color: orange;">Borrador</span>')
        else:
            return format_html('<span style="color: green;">Confirmado</span>')
    draft_status.short_description = _('Estado')
    
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
    
    # Acciones personalizadas
    actions = ['confirm_movements', 'mark_as_draft']
    
    def confirm_movements(self, request, queryset):
        updated = queryset.filter(draft=True).update(draft=False)
        
        # Actualizar inventario para los productos afectados
        product_ids = queryset.values_list('product_id', flat=True).distinct()
        for product_id in product_ids:
            inventory, created = InventoryStatus.objects.get_or_create(
                product_id=product_id,
                defaults={'current_stock': 0}
            )
            inventory.update_stock()
        
        self.message_user(request, _('Se confirmaron {} movimientos de inventario.').format(updated))
    confirm_movements.short_description = _('Confirmar movimientos seleccionados')
    
    def mark_as_draft(self, request, queryset):
        updated = queryset.filter(draft=False).update(draft=True)
        
        # Actualizar inventario para los productos afectados
        product_ids = queryset.values_list('product_id', flat=True).distinct()
        for product_id in product_ids:
            inventory, created = InventoryStatus.objects.get_or_create(
                product_id=product_id,
                defaults={'current_stock': 0}
            )
            inventory.update_stock()
        
        self.message_user(request, _('Se marcaron {} movimientos como borrador.').format(updated))
    mark_as_draft.short_description = _('Marcar seleccionados como borrador')
    
    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        try:
            extra_context['report_url'] = reverse('inventory:inventory_report')
        except:
            # Si la URL no está disponible, no hacemos nada
            pass
        return super().changelist_view(request, extra_context=extra_context)


# urls.py básico
from django.urls import path
from . import views

app_name = 'inventory'

urlpatterns = [
    # Implementaremos vistas básicas primero
]


# views.py básico
from django.shortcuts import render
from django.contrib.admin.views.decorators import staff_member_required

# Implementaremos vistas básicas primero


# signals.py
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from services.models import Product
from .models import InventoryMovement, InventoryStatus

@receiver(post_save, sender=Product)
def create_inventory_status(sender, instance, created, **kwargs):
    """Crea un estado de inventario cuando se crea un nuevo producto"""
    if created:
        InventoryStatus.objects.get_or_create(
            product=instance,
            defaults={'current_stock': instance.stock}
        )

@receiver(post_save, sender=InventoryMovement)
def update_inventory_after_movement(sender, instance, **kwargs):
    """Actualiza el inventario después de un movimiento, si no es borrador"""
    if not instance.draft:
        inventory, created = InventoryStatus.objects.get_or_create(
            product=instance.product,
            defaults={'current_stock': 0}
        )
        inventory.update_stock()

@receiver(post_delete, sender=InventoryMovement)
def update_inventory_after_movement_delete(sender, instance, **kwargs):
    """Actualiza el inventario después de eliminar un movimiento"""
    try:
        inventory = InventoryStatus.objects.get(product=instance.product)
        inventory.update_stock()
    except InventoryStatus.DoesNotExist:
        pass


# apps.py
from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _

class InventoryConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'inventory'
    verbose_name = _('Inventario')
    
    def ready(self):
        # Importar señales
        import inventory.signals
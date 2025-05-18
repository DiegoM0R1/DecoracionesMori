from django.contrib import admin

# Register your models here.
from .models import InventoryMovement

@admin.register(InventoryMovement)
class InventoryMovementAdmin(admin.ModelAdmin):
    list_display = ('product', 'quantity', 'movement_type', 'document_reference', 'created_at')
    list_filter = ('movement_type', 'product')
    search_fields = ('product__name', 'document_reference', 'notes')
    ordering = ('-created_at',)
    date_hierarchy = 'created_at'
    fieldsets = (
        (None, {
            'fields': ('product', 'quantity', 'movement_type', 'document_reference', 'invoice_item', 'notes')
        }),
        ('Date Information', {
            'fields': ('created_at',),
            'classes': ('collapse',),
        }),
    )

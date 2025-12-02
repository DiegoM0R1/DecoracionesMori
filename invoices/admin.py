# invoices/admin.py
from django.contrib import admin
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from .models import Invoice, InvoiceItem
from django.urls import reverse
from django import forms
from django.db import models

class InvoiceItemInline(admin.TabularInline):
    model = InvoiceItem
    extra = 1
    fields = ['item_type', 'service', 'product', 'description', 'quantity', 'unit_price', 'discount', 'subtotal']
    readonly_fields = ('subtotal',)
    
    # Script para mostrar/ocultar campos según tipo de ítem
    class Media:
        js = ('admin/js/invoiceitem_admin.js',)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        formfield = super().formfield_for_foreignkey(db_field, request, **kwargs)
    
        # Cuando el formulario se renderiza, añadir JavaScript inline para cada campo
        if db_field.name == 'product':
            formfield.widget.attrs['onchange'] = """
                (function(){
                    var productId = this.value;
                    if (productId) {
                        var row = this.closest('tr');
                        var priceField = row.querySelector('input[name$="-unit_price"]');
                        fetch('/api/products/' + productId + '/')
                            .then(response => response.json())
                            .then(data => {
                            if (priceField) {
                                    priceField.value = data.price_per_unit;
                                }
                            });
                    }
                })();
            """
        elif db_field.name == 'service':
            # Similar para servicios...
            pass
        
        return formfield

@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ('get_invoice_number', 'date_issued', 'client', 'total', 
                    'advance_payment', 'pending_balance', 'status', 'payment_method', 
                    'inventory_status', 'register_payment_button')

    list_filter = ('invoice_type','status', 'payment_method', 'date_issued', 'inventory_processed')
    search_fields = ('series', 'number', 'client__first_name', 'client__last_name', 'client__dni')
    readonly_fields = ('subtotal', 'igv', 'total', 'pending_balance', 'inventory_processed')
    
    fieldsets = (
        (_('Información del Documento'), {
            'fields': (('invoice_type', 'series', 'number'), 'date_issued', 'status', 'appointment')
        }),
        (_('Cliente'), {
            'fields': ('client',)
        }),
        (_('Pago'), {
            'fields': ('payment_method', 'payment_reference', 'advance_payment', 'pending_balance')
        }),
        (_('Totales'), {
            'fields': (('subtotal', 'igv', 'total'),)
        }),
        (_('Control de Inventario'), {
            'fields': ('inventory_processed',),
            'classes': ('collapse',),
        }),
        (_('Observaciones'), {
            'fields': ('notes',)
        }),
    )
    
    inlines = [InvoiceItemInline]
    actions = ['reprocess_inventory', 'mark_inventory_processed']
    
    def get_invoice_number(self, obj):
        return f"{obj.series}-{obj.number or '(borrador)'}"
    get_invoice_number.short_description = _('Número de Boleta')
    
    def inventory_status(self, obj):
        """Muestra el estado del inventario para esta boleta"""
        if obj.status != 'pagada':
            return format_html('<span style="color: gray;">⏸️ Pendiente de pago</span>')
        elif obj.inventory_processed:
            return format_html('<span style="color: green;">✅ Procesado</span>')
        else:
            return format_html('<span style="color: red;">❌ No procesado</span>')
    inventory_status.short_description = _('Inventario')
    
    def register_payment_button(self, obj):
        """Botón para registrar pago pendiente"""
        if obj.status != 'anulada' and obj.pending_balance > 0:
            return format_html(
                '<a href="{}" class="button" style="background-color: #28a745; color: white;">'
                '<i class="fas fa-money-bill"></i> Registrar Pago</a>',
                reverse('invoices:register_pending_payment', args=[obj.pk])
            )
        elif obj.status != 'anulada':
            buttons = format_html(
                '<a href="{}" target="_blank" class="button" style="background-color: #17a2b8; color: white;">'
                '<i class="fas fa-print"></i> Imprimir</a>',
                reverse('invoices:print_invoice', args=[obj.pk])
            )
            
            # Si está pagada pero no se procesó el inventario, agregar botón para reprocesar
            if obj.status == 'pagada' and not obj.inventory_processed:
                buttons += format_html(
                    ' <a href="#" onclick="processInventory({})" class="button" style="background-color: #ffc107; color: black;">'
                    '<i class="fas fa-sync"></i> Procesar Inventario</a>',
                    obj.pk
                )
            
            return buttons
        return "-"

    register_payment_button.short_description = "Acciones"
    register_payment_button.allow_tags = True
    
    def reprocess_inventory(self, request, queryset):
        """Acción para reprocesar el inventario de boletas seleccionadas"""
        processed_count = 0
        for invoice in queryset.filter(status='pagada'):
            if not invoice.inventory_processed:
                invoice.process_inventory()
                processed_count += 1
        
        if processed_count > 0:
            self.message_user(
                request, 
                f'Se procesó el inventario para {processed_count} boleta(s).'
            )
        else:
            self.message_user(
                request, 
                'No se encontraron boletas elegibles para procesar inventario.',
                level='warning'
            )
    reprocess_inventory.short_description = _('Procesar inventario para boletas pagadas')
    
    def mark_inventory_processed(self, request, queryset):
        """Acción para marcar manualmente como procesado (para casos especiales)"""
        updated = queryset.update(inventory_processed=True)
        self.message_user(
            request, 
            f'Se marcaron {updated} boleta(s) como inventario procesado.'
        )
    mark_inventory_processed.short_description = _('Marcar inventario como procesado')
    
    def save_model(self, request, obj, form, change):
        # Asignar el usuario que guarda como creador si es nuevo
        if not change:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)

    class Media:
        js = ('admin/js/invoiceitem_admin.js',)
        
        # JavaScript adicional para el botón de procesar inventario
        extra_js = """
        <script>
        function processInventory(invoiceId) {
            if (confirm('¿Está seguro de que desea procesar el inventario para esta boleta?')) {
                fetch('/admin/invoices/invoice/' + invoiceId + '/process-inventory/', {
                    method: 'POST',
                    headers: {
                        'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value,
                        'Content-Type': 'application/json',
                    },
                })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        alert('Inventario procesado correctamente');
                        location.reload();
                    } else {
                        alert('Error al procesar inventario: ' + data.error);
                    }
                })
                .catch(error => {
                    alert('Error al procesar inventario');
                    console.error('Error:', error);
                });
            }
        }
        </script>
        """
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
        
        return formfield  # Esta línea faltaba

@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ('get_invoice_number', 'date_issued', 'client', 'total', 
                    'advance_payment', 'pending_balance', 'status', 'payment_method', 'register_payment_button')


    list_filter = ('status', 'payment_method', 'date_issued')
    search_fields = ('series', 'number', 'client__first_name', 'client__last_name', 'client__dni')
    readonly_fields = ('subtotal', 'igv', 'total', 'pending_balance')
    
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
        (_('Observaciones'), {
            'fields': ('notes',)
        }),
    )
    
    inlines = [InvoiceItemInline]
    
    def get_invoice_number(self, obj):
        return f"{obj.series}-{obj.number or '(borrador)'}"
    get_invoice_number.short_description = _('Número de Boleta')
    
    def register_payment_button(self, obj):
        """Botón para registrar pago pendiente"""
        if obj.status != 'anulada' and obj.pending_balance > 0:
            return format_html(
                '<a href="{}" class="button" style="background-color: #28a745; color: white;">'
                '<i class="fas fa-money-bill"></i> Registrar Pago</a>',
                reverse('invoices:register_pending_payment', args=[obj.pk])
            )
        elif obj.status != 'anulada':
            return format_html(
                '<a href="{}" target="_blank" class="button" style="background-color: #17a2b8; color: white;">'
                '<i class="fas fa-print"></i> Imprimir</a>',
                reverse('invoices:print_invoice', args=[obj.pk])
            )
        return "-"

    register_payment_button.short_description = "Acciones"
    register_payment_button.allow_tags = True
    
    def save_model(self, request, obj, form, change):
        # Asignar el usuario que guarda como creador si es nuevo
        if not change:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)

    class Media:
        js = ('admin/js/invoiceitem_admin.js',) 
from django.contrib import admin
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from .models import Invoice, InvoiceItem
from django.urls import reverse
from django import forms
from django.contrib import messages
# Importamos las utilidades de correo
from appointments.utils import (
    send_appointment_confirmation_email, 
    send_invoice_generated_email, 
    send_advance_payment_confirmation_email, 
    send_full_payment_confirmation_email
)

class InvoiceItemInline(admin.TabularInline):
    model = InvoiceItem
    extra = 1
    fields = ['item_type', 'service', 'product', 'description', 'quantity', 'unit_price', 'discount', 'subtotal']
    readonly_fields = ('subtotal',)
    
    class Media:
        js = ('admin/js/invoiceitem_admin.js',)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        formfield = super().formfield_for_foreignkey(db_field, request, **kwargs)
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
    
    # --- MÉTODO SAVE_MODEL ROBUSTECIDO ---
    def save_model(self, request, obj, form, change):
        # 1. Asignar creador si es nuevo
        if not change:
            obj.created_by = request.user
            
        # --- A. CÁLCULOS PREVIOS ---
        current_total = float(obj.total) if obj.total else 0.0
        current_advance = float(obj.advance_payment) if obj.advance_payment else 0.0
        pending = current_total - current_advance
        
        # Banderas de estado
        is_full_payment = (pending <= 0.5 and current_total > 0)
        is_advance_payment = (current_advance >= 50)
        
        # --- B. CAMBIO DE ESTADO AUTOMÁTICO (ANTES DE GUARDAR) ---
        # Esto soluciona tu problema:
        
        if is_full_payment:
            obj.status = 'pagada'
        elif is_advance_payment and obj.status == 'borrador':
            # Si hay plata (>=50) y no es pago total, deja de ser borrador
            obj.status = 'emitida'

        # --- C. DETECTAR SI DEBEMOS ENVIAR CORREOS ---
        # Necesitamos saber cómo estaba ANTES de guardar para no repetir correos
        send_full_mail = False
        send_advance_mail = False
        
        if change:
            try:
                old_obj = Invoice.objects.get(pk=obj.pk)
                old_advance = float(old_obj.advance_payment) if old_obj.advance_payment else 0.0
                was_paid = (old_obj.status == 'pagada')
                
                # CORRECCIÓN: Miramos el ESTADO REAL (obj.status), no solo el cálculo matemático.
                # Si ahora dice 'pagada' y antes no lo decía -> ENVÍA EL CORREO.
                if obj.status == 'pagada' and not was_paid:
                    send_full_mail = True
                
                # Para el adelanto, mantenemos la lógica matemática para evitar falsos positivos
                elif is_advance_payment and old_advance < 50 and obj.status != 'pagada':
                    send_advance_mail = True
                    
            except Invoice.DoesNotExist:
                pass
        else:
            # Nueva boleta
            if obj.status == 'pagada': # Corrección aquí también
                send_full_mail = True
            elif is_advance_payment:
                send_advance_mail = True

        # --- D. GUARDAR EN BASE DE DATOS ---
        # Aquí se guarda el estado 'emitida' o 'pagada' que asignamos arriba
        super().save_model(request, obj, form, change)
        
        # --- E. ENVIAR CORREOS Y ACTUALIZAR CITA ---
        if obj.appointment:
            # 1. Actualizar estado de la Cita
            if (is_full_payment or is_advance_payment) and obj.appointment.status == 'pending':
                obj.appointment.status = 'confirmed'
                obj.appointment.save()

            # 2. Enviar Correos (Con manejo de errores visual)
            if send_full_mail:
                try:
                    send_full_payment_confirmation_email(request, obj)
                    self.message_user(request, "🎉 Deuda saldada: Correo final enviado.", level=messages.SUCCESS)
                except Exception as e:
                    self.message_user(request, f"⚠️ Boleta guardada, pero falló el correo: {e}", level=messages.ERROR)
            
            elif send_advance_mail:
                try:
                    send_advance_payment_confirmation_email(request, obj)
                    self.message_user(request, "✅ Adelanto registrado: Correo enviado.", level=messages.INFO)
                except Exception as e:
                    self.message_user(request, f"⚠️ Adelanto guardado, pero falló el correo: {e}", level=messages.ERROR)

    def get_invoice_number(self, obj):
        return f"{obj.series}-{obj.number or '(borrador)'}"
    get_invoice_number.short_description = _('Número de Boleta')
    
    def inventory_status(self, obj):
        if obj.status != 'pagada':
            return format_html('<span style="color: gray;"> Pendiente de pago</span>')
        elif obj.inventory_processed:
            return format_html('<span style="color: green;"> Procesado</span>')
        else:
            return format_html('<span style="color: red;"> No procesado</span>')
    inventory_status.short_description = _('Inventario')
    
    def register_payment_button(self, obj):
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
        processed_count = 0
        for invoice in queryset.filter(status='pagada'):
            if not invoice.inventory_processed:
                invoice.process_inventory()
                processed_count += 1
        
        if processed_count > 0:
            self.message_user(request, f'Se procesó el inventario para {processed_count} boleta(s).')
        else:
            self.message_user(request, 'No se encontraron boletas elegibles para procesar inventario.', level='warning')
    reprocess_inventory.short_description = _('Procesar inventario para boletas pagadas')
    
    def mark_inventory_processed(self, request, queryset):
        updated = queryset.update(inventory_processed=True)
        self.message_user(request, f'Se marcaron {updated} boleta(s) como inventario procesado.')
    mark_inventory_processed.short_description = _('Marcar inventario como procesado')

    class Media:
        js = ('admin/js/invoiceitem_admin.js',)
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
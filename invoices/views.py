# invoices/views.py
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.admin.views.decorators import staff_member_required
from django.http import HttpResponse
from django.template.loader import render_to_string
from django.utils import timezone
from django.contrib import messages
from django.contrib import admin
from decimal import Decimal
from .models import Invoice

@staff_member_required
def print_invoice(request, invoice_id):
    """Vista para imprimir una boleta"""
    invoice = get_object_or_404(Invoice, id=invoice_id)
    
    # Renderizar directamente el HTML para imprimir desde el navegador
    return render(request, 'invoices/invoice_print.html', {
        'invoice': invoice,
        'items': invoice.invoiceitem_set.all(),
        'today': timezone.now(),
        'company_name': 'Decoraciones Mori',
        'company_ruc': '20123456789',  # Reemplazar con el RUC real
        'company_address': 'Av. Principal 123, Chiclayo',  # Reemplazar con dirección real
        'print_view': True,  # Indicar que es la vista de impresión
    })

@staff_member_required
def register_pending_payment(request, invoice_id):
    """Vista para registrar el pago pendiente de una boleta"""
    invoice = get_object_or_404(Invoice, id=invoice_id)
    
    # Guardar el estado anterior para detectar cambios
    previous_status = invoice.status
    previous_balance = invoice.pending_balance
    
    if request.method == 'POST':
        amount_paid = Decimal(request.POST.get('amount_paid', 0))
        payment_method = request.POST.get('payment_method', 'efectivo')
        payment_reference = request.POST.get('payment_reference', '')
        
        # Validar que el monto no sea mayor que el saldo pendiente
        if amount_paid > invoice.pending_balance:
            messages.error(
                request,
                f"El monto a pagar (S/ {amount_paid}) no puede ser mayor que el saldo pendiente (S/ {invoice.pending_balance})."
            )
            return render(request, 'admin/invoices/register_payment.html', {
                'invoice': invoice,
                'title': f'Registrar pago para boleta #{invoice.number or "(borrador)"}',
                'site_header': 'Administración',
                'has_permission': True,
                'is_popup': False,
                'is_nav_sidebar_enabled': True,
                'available_apps': admin.site.get_app_list(request),
                'opts': invoice._meta,
                'error_message': f"El monto a pagar no puede ser mayor que el saldo pendiente."
            })
        
        # Actualizar adelanto y saldo pendiente
        invoice.advance_payment += amount_paid
        invoice.pending_balance = invoice.total - invoice.advance_payment
        
        # Actualizar método de pago y referencia
        invoice.payment_method = payment_method
        if payment_reference:
            invoice.payment_reference = payment_reference
        
        # Si se pagó completamente, cambiar estado
        if invoice.pending_balance <= 0:
            invoice.status = 'pagada'
            # Si hay cita asociada, marcarla como completada
            if invoice.appointment and invoice.appointment.status != 'completed':
                invoice.appointment.status = 'completed'
                invoice.appointment.save(update_fields=['status'])
        
        # Guardar la boleta (esto activará el proceso de inventario si cambia a 'pagada')
        invoice.save()
        
        # Mensajes informativos
        success_message = f"Pago de S/ {amount_paid} registrado correctamente mediante {dict(Invoice.PAYMENT_METHOD_CHOICES).get(payment_method, payment_method)}."
        
        # Si cambió a pagada y se procesó el inventario, agregar información adicional
        if previous_status != 'pagada' and invoice.status == 'pagada':
            product_items = invoice.invoiceitem_set.filter(item_type='product', product__isnull=False)
            if product_items.exists():
                products_affected = product_items.count()
                success_message += f" Se actualizó el inventario para {products_affected} producto(s)."
        
        messages.success(request, success_message)
        return redirect('admin:invoices_invoice_change', invoice.id)
    
    return render(request, 'admin/invoices/register_payment.html', {
        'invoice': invoice,
        'title': f'Registrar pago para boleta #{invoice.number or "(borrador)"}',
        'site_header': 'Administración',
        'has_permission': True,
        'is_popup': False,
        'is_nav_sidebar_enabled': True,
        'available_apps': admin.site.get_app_list(request),
        'opts': invoice._meta,
    })
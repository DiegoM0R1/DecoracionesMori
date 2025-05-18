# invoices/views.py
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.admin.views.decorators import staff_member_required
from django.http import HttpResponse
from django.template.loader import render_to_string
from django.utils import timezone
from django.contrib import messages
from django.contrib import admin  # Añade esta importación
from decimal import Decimal
from .models import Invoice

# Eliminamos la importación de weasyprint
# import weasyprint  

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
    
    if request.method == 'POST':
        amount_paid = Decimal(request.POST.get('amount_paid', 0))
        payment_method = request.POST.get('payment_method', 'efectivo')
        payment_reference = request.POST.get('payment_reference', '')
        
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
        
        invoice.save()
        
        messages.success(
            request, 
            f"Pago de S/ {amount_paid} registrado correctamente mediante {dict(Invoice.PAYMENT_METHOD_CHOICES).get(payment_method, payment_method)}."
        )
        return redirect('admin:invoices_invoice_change', invoice.id)
    
    # Versión corregida - no intentamos acceder a request.admin_site
    return render(request, 'admin/invoices/register_payment.html', {
        'invoice': invoice,
        'title': f'Registrar pago para boleta #{invoice.number or "(borrador)"}',
        'site_header': 'Administración',
        'has_permission': True,
        'is_popup': False,
        'is_nav_sidebar_enabled': True,
        # No usamos request.admin_site sino admin.site
        'available_apps': admin.site.get_app_list(request),
        'opts': invoice._meta,
    })
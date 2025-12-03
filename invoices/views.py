from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.admin.views.decorators import staff_member_required
from django.http import HttpResponse, HttpResponseForbidden
from django.template.loader import render_to_string
from django.utils import timezone
from django.contrib import messages
from django.contrib import admin
from django.contrib.auth.decorators import login_required
from decimal import Decimal
from .models import Invoice

# --- IMPORTANTE: Importamos la función de envío de correo ---
# Asegúrate de que este import apunte correctamente a donde definiste la función
from appointments.utils import send_full_payment_confirmation_email 

@staff_member_required
def print_invoice(request, invoice_id):
    """Vista para imprimir una boleta"""
    invoice = get_object_or_404(Invoice, id=invoice_id)
    
    return render(request, 'invoices/invoice_print.html', {
        'invoice': invoice,
        'items': invoice.invoiceitem_set.all(),
        'today': timezone.now(),
        'company_name': 'Decoraciones Mori',
        'company_ruc': '20123456789',  
        'company_address': 'Av. Principal 123, Chiclayo', 
        'print_view': True, 
    })

@staff_member_required
def register_pending_payment(request, invoice_id):
    """Vista para registrar el pago pendiente de una boleta"""
    invoice = get_object_or_404(Invoice, id=invoice_id)
    
    # Guardar el estado anterior para detectar cambios
    previous_status = invoice.status
    
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
            # Re-renderizamos el formulario con el error
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
        
        # 1. Actualizar adelanto y saldo pendiente
        invoice.advance_payment += amount_paid
        invoice.pending_balance = invoice.total - invoice.advance_payment
        
        # 2. Actualizar método de pago y referencia
        invoice.payment_method = payment_method
        if payment_reference:
            invoice.payment_reference = payment_reference
        
        # 3. VERIFICAR PAGO TOTAL
        email_sent_success = False
        email_error_msg = ""
        
        if invoice.pending_balance <= 0:
            invoice.status = 'pagada'
            
            # Lógica de Cita: Mantenemos tu lógica de 'completed' 
            # (Aunque si es un pago previo al servicio, quizás debería ser 'confirmed')
            if invoice.appointment:
                 # Si la cita estaba pendiente, la confirmamos/completamos
                 if invoice.appointment.status == 'pending':
                     invoice.appointment.status = 'confirmed' # Sugiero 'confirmed' al pagar, 'completed' es al terminar el trabajo
                     invoice.appointment.save()
                 elif invoice.appointment.status != 'completed':
                     # Si ya estaba confirmada, quizás aquí la pasas a completada si es pago contra entrega
                     invoice.appointment.status = 'completed'
                     invoice.appointment.save(update_fields=['status'])

            # Guardamos para asegurar que el estado 'pagada' esté en BD antes de enviar correo
            invoice.save()
            
            # --- AQUÍ ESTÁ LA MAGIA: ENVÍO DE CORREO ---
            try:
                print(f"📧 Enviando correo de pago total para Factura #{invoice.id}")
                send_full_payment_confirmation_email(request, invoice)
                email_sent_success = True
            except Exception as e:
                print(f"❌ Error enviando correo: {e}")
                email_error_msg = str(e)
        else:
            # Si no es pago total, solo guardamos
            invoice.save()
        
        # 4. Mensajes informativos
        success_message = f"Pago de S/ {amount_paid} registrado correctamente mediante {dict(Invoice.PAYMENT_METHOD_CHOICES).get(payment_method, payment_method)}."
        
        # Mensaje sobre inventario
        if previous_status != 'pagada' and invoice.status == 'pagada':
            product_items = invoice.invoiceitem_set.filter(item_type='product', product__isnull=False)
            if product_items.exists():
                products_affected = product_items.count()
                success_message += f" Se actualizó el inventario para {products_affected} producto(s)."
        
        # Mensaje sobre el correo
        if email_sent_success:
            success_message += " ✉️ Se envió el correo de confirmación al cliente."
        elif email_error_msg:
            messages.warning(request, f"Pago registrado, pero falló el envío del correo: {email_error_msg}")
        
        messages.success(request, success_message)
        return redirect('admin:invoices_invoice_change', invoice.id)
    
    # GET Request
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

@login_required
def client_print_invoice(request, invoice_id):
    """
    Vista para que el cliente descargue su propio comprobante.
    """
    invoice = get_object_or_404(Invoice, id=invoice_id)
    
    if invoice.client != request.user and not request.user.is_staff:
        return HttpResponseForbidden("No tiene permisos para ver este comprobante.")
    
    return render(request, 'invoices/invoice_print.html', {
        'invoice': invoice,
        'items': invoice.invoiceitem_set.all(),
        'today': timezone.now(),
        'company_name': 'Decoraciones Mori', 
        'print_view': True,
    })
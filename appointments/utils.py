from django.utils import timezone
from django.contrib import messages
from datetime import timedelta, datetime, time
from .models import Appointment
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings
from django.urls import reverse

# ==========================================
# LÓGICA DE MANTENIMIENTO (CITAS VENCIDAS)
# ==========================================
def check_and_cancel_expired_appointments(request=None):
    now = timezone.now()
    start_date = now - timedelta(days=730)
    end_date = now + timedelta(days=5)
    
    pending_appointments = Appointment.objects.filter(
        status='pending',
        appointment_date__range=[start_date.date(), end_date.date()]
    )

    cancelled_count = 0

    for appointment in pending_appointments:
        if appointment.appointment_date:
            appt_time = appointment.appointment_time if appointment.appointment_time else time(23, 59)
            appt_datetime_naive = datetime.combine(appointment.appointment_date, appt_time)
            
            try:
                if timezone.is_aware(now):
                    appt_datetime = timezone.make_aware(appt_datetime_naive, timezone.get_current_timezone())
                else:
                    appt_datetime = appt_datetime_naive
            except Exception:
                appt_datetime = appt_datetime_naive

            deadline = appt_datetime - timedelta(hours=24)
            now_ts = now.timestamp()
            deadline_ts = deadline.timestamp()

            if now_ts > deadline_ts:
                appointment.status = 'cancelled'
                appointment.notes = (appointment.notes or "") + f"\n[AUTO] Cancelada el {now.strftime('%d/%m %H:%M')}. Deadline era: {deadline.strftime('%d/%m %H:%M')}"
                appointment.save()
                cancelled_count += 1
            else:
                if request and (deadline_ts - now_ts) < 172800: 
                    time_left = (deadline_ts - now_ts) / 3600
                    messages.info(request, f"Diagnóstico Cita #{appointment.id}: No vencida. Faltan {time_left:.1f} horas para que el sistema la cancele.")

    return cancelled_count


# ==========================================
# LÓGICA DE ENVÍO DE CORREOS
# ==========================================

def send_html_email(subject, template_name, context, recipient_list):
    """Función auxiliar para enviar correos HTML con depuración."""
    try:
        html_message = render_to_string(template_name, context)
        plain_message = strip_tags(html_message)
        
        send_mail(
            subject,
            plain_message,
            settings.DEFAULT_FROM_EMAIL,
            recipient_list,
            html_message=html_message,
            fail_silently=False, 
        )
        print(f"✅ CORREO ENVIADO: '{subject}' a {recipient_list}")
    except Exception as e:
        print(f"❌ ERROR CRÍTICO ENVIANDO CORREO '{subject}': {e}")


def send_appointment_received_email(request, appointment):
    """1. Solicitud Recibida"""
    subject = f'Hemos recibido tu solicitud - Cita #{appointment.id}'
    try:
        web_link = request.build_absolute_uri(
            reverse('appointments:appointment_detail', kwargs={'appointment_id': appointment.id})
        )
    except Exception:
        web_link = "#"

    context = {
        'appointment': appointment,
        'client': appointment.client,
        'service': appointment.service,
        'web_link': web_link
    }
    send_html_email(subject, 'emails/appointment_received.html', context, [appointment.client.email])


def send_appointment_confirmation_email(request, appointment):
    """2. Confirmación de Cita"""
    subject = f'¡Tu Cita #{appointment.id} ha sido CONFIRMADA!'
    
    # Link al detalle de la cita en la web
    try:
        web_link = request.build_absolute_uri(
            reverse('appointments:appointment_detail', kwargs={'appointment_id': appointment.id})
        )
    except Exception:
        web_link = "#"

    context = {
        'appointment': appointment,
        'client': appointment.client,
        'service': appointment.service,
        'date': appointment.appointment_date,
        'time': appointment.appointment_time,
        'web_link': web_link 
    }
    send_html_email(subject, 'emails/appointment_confirmed.html', context, [appointment.client.email])


def send_invoice_generated_email(request, invoice):
    """3. Aviso de documento legal generado"""
    doc_type = invoice.get_invoice_type_display()
    subject = f'Documento Electrónico {invoice.series}-{invoice.number}'
    
    # CORRECCIÓN: Mandamos al cliente a ver el detalle de su cita donde sale la boleta
    try:
        download_link = request.build_absolute_uri(
            reverse('appointments:appointment_detail', kwargs={'appointment_id': invoice.appointment.id})
        )
    except Exception:
        download_link = "#"
    
    context = {
        'invoice': invoice,
        'client': invoice.client,
        'doc_type': doc_type,
        'amount': invoice.total,
        'download_link': download_link
    }
    send_html_email(subject, 'emails/invoice_generated.html', context, [invoice.client.email])


def send_appointment_cancelled_email(request, appointment):
    """4. Cancelación"""
    subject = f'Cita Cancelada #{appointment.id} - Decoraciones Mori'
    try:
        rebook_link = request.build_absolute_uri(reverse('appointments:request', args=[appointment.service.id]))
    except Exception:
        rebook_link = "#"

    context = {
        'appointment': appointment,
        'client': appointment.client,
        'service': appointment.service,
        'rebook_link': rebook_link
    }
    send_html_email(subject, 'emails/appointment_cancelled.html', context, [appointment.client.email])


def send_advance_payment_confirmation_email(request, invoice):
    """
    5. Confirmación del ADELANTO.
    CORREGIDO: El link lleva al 'appointment_detail' (Panel del Cliente).
    """
    subject = f'✅ Adelanto Recibido - Cita Confirmada #{invoice.appointment.id}'
    
    try:
        # Apuntamos a la vista 'appointment_detail' que está en tu views.py
        dashboard_link = request.build_absolute_uri(
            reverse('appointments:appointment_detail', kwargs={'appointment_id': invoice.appointment.id})
        )
    except Exception as e:
        print(f"⚠️ Error generando link al dashboard: {e}")
        dashboard_link = "#"

    # Calculamos saldos
    total = float(invoice.total) if invoice.total else 0.0
    paid = float(invoice.advance_payment) if invoice.advance_payment else 0.0
    pending = total - paid

    context = {
        'client': invoice.client,
        'appointment': invoice.appointment,
        'amount_paid': paid,
        'total': total,
        'pending_balance': pending,
        'invoice_number': f"{invoice.series}-{invoice.number}",
        'download_link': dashboard_link,  # <--- Este link va al sitio web del cliente
        'doc_type': invoice.get_invoice_type_display()
    }
    
    send_html_email(subject, 'emails/advance_payment_confirmed.html', context, [invoice.client.email])


def send_full_payment_confirmation_email(request, invoice):
    """
    6. Confirmación de PAGO TOTAL.
    CORREGIDO: El link lleva al 'appointment_detail' (Panel del Cliente).
    """
    print(f"📧 Preparando correo de PAGO TOTAL para factura #{invoice.id}...")
    
    subject = f'🎉 Pago Completado - Comprobante {invoice.series}-{invoice.number}'
    
    try:
        # Apuntamos a la vista 'appointment_detail'
        dashboard_link = request.build_absolute_uri(
            reverse('appointments:appointment_detail', kwargs={'appointment_id': invoice.appointment.id})
        )
    except Exception as e:
        print(f"⚠️ Error generando link al dashboard: {e}")
        dashboard_link = "#"
    
    context = {
        'client': invoice.client,
        'invoice': invoice,
        'invoice_number': f"{invoice.series}-{invoice.number}",
        'total': invoice.total,
        'download_link': dashboard_link # <--- Este link va al sitio web del cliente
    }
    
    send_html_email(subject, 'emails/full_payment_confirmed.html', context, [invoice.client.email])
# appointments/utils.py
from django.utils import timezone
from django.contrib import messages
from datetime import timedelta, datetime, time
from .models import Appointment
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings

# --- TU LÓGICA EXISTENTE ---
def check_and_cancel_expired_appointments(request=None):
    """
    Verifica citas vencidas. (Tu código original se mantiene aquí)
    """
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

# --- NUEVA LÓGICA DE CORREOS ---
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings
from django.urls import reverse

# --- LÓGICA DE CORREOS ---

def send_html_email(subject, template_name, context, recipient_list):
    """Función auxiliar para enviar correos HTML"""
    try:
        html_message = render_to_string(template_name, context)
        plain_message = strip_tags(html_message)
        
        send_mail(
            subject,
            plain_message,
            settings.DEFAULT_FROM_EMAIL, # Asegúrate de tener esto en settings.py
            recipient_list,
            html_message=html_message,
            fail_silently=True,
        )
        print(f"Correo '{subject}' enviado correctamente a {recipient_list}")
    except Exception as e:
        print(f"Error enviando correo: {e}")

def send_appointment_received_email(request, appointment):
    """1. Correo cuando el cliente envía el formulario (Solicitud Recibida)"""
    subject = f'Hemos recibido tu solicitud - Cita #{appointment.id}'
    
    context = {
        'appointment': appointment,
        'client': appointment.client,
        'service': appointment.service,
        # Si tienes una vista para ver el detalle en web, genérala aquí
        'web_link': request.build_absolute_uri(reverse('appointments:appointment_list'))
    }
    
    send_html_email(subject, 'emails/appointment_received.html', context, [appointment.client.email])

def send_appointment_confirmation_email(request, appointment):
    """2. Correo cuando el administrador confirma la cita"""
    subject = f'¡Tu Cita #{appointment.id} ha sido CONFIRMADA!'
    
    context = {
        'appointment': appointment,
        'client': appointment.client,
        'service': appointment.service,
        'date': appointment.appointment_date,
        'time': appointment.appointment_time,
    }
    
    send_html_email(subject, 'emails/appointment_confirmed.html', context, [appointment.client.email])

def send_invoice_generated_email(request, invoice):
    """3. Correo cuando se genera la boleta/factura (con enlace de descarga)"""
    doc_type = invoice.get_invoice_type_display()
    subject = f'Tu {doc_type} {invoice.series}-{invoice.number} está disponible'
    
    # Generamos el enlace absoluto (http://tusitio.com/...) para que funcione desde Gmail
    download_link = request.build_absolute_uri(reverse('invoices:client_print_invoice', args=[invoice.id]))
    
    context = {
        'invoice': invoice,
        'client': invoice.client,
        'doc_type': doc_type,
        'amount': invoice.total,
        'download_link': download_link # <--- Esto es lo que permite descargar
    }
    
    send_html_email(subject, 'emails/invoice_generated.html', context, [invoice.client.email])

# (Mantén aquí abajo tu función check_and_cancel_expired_appointments sin cambios)
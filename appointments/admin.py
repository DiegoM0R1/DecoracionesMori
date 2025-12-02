# appointments/admin.py
from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from .models import Appointment, WorkScheduleTemplate, ScheduledWorkDay
from django.contrib import messages # No se usa directamente en el admin modificado, pero está bien tenerla
from django.shortcuts import get_object_or_404, redirect # No se usa directamente, pero está bien tenerla
from urllib.parse import quote
# Estas importaciones las necesitaremos para el contexto en changelist_view
from services.models import Service # Asegúrate que esta app y modelo existan
from django.contrib.auth import get_user_model

User = get_user_model() # Obtenemos el modelo User

# --- Admin para Modelos de Horario ---

@admin.register(WorkScheduleTemplate)
class WorkScheduleTemplateAdmin(admin.ModelAdmin):
    list_display = ('get_day_of_week_display', 'start_time', 'end_time', 'is_working_day')
    list_editable = ('start_time', 'end_time', 'is_working_day')
    ordering = ('day_of_week',)

    def get_day_of_week_display(self, obj):
        return obj.get_day_of_week_display()
    get_day_of_week_display.short_description = _('Día de la semana')

from .utils import check_and_cancel_expired_appointments 

# --- MODIFICACIÓN EN ScheduledWorkDayAdmin ---
@admin.register(ScheduledWorkDay)
class ScheduledWorkDayAdmin(admin.ModelAdmin):
    change_list_template = 'admin/appointments/calendar.html'

    def changelist_view(self, request, extra_context=None):
        from .utils import check_and_cancel_expired_appointments
        
        # ---> CAMBIO AQUÍ: Pasamos 'request' para ver los mensajes <--
        cancelled = check_and_cancel_expired_appointments(request)
        
        if cancelled > 0:
            from django.contrib import messages
            messages.warning(request, f"MANTENIMIENTO: Se han cancelado {cancelled} citas vencidas automáticamente.")
            
        return super().changelist_view(request, extra_context=extra_context)


    # La función get_day_name ya no es estrictamente necesaria aquí si no usamos list_display
    # def get_day_name(self, obj):
    #     days = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
    #     return days[obj.date.weekday()]
    # get_day_name.short_description = _('Día')

# --- Admin para Citas (Modificado de tu código original) ---
# (Este AppointmentAdmin sigue como lo tenías, mostrando la lista de tabla estándar)
# A MENOS que también quieras cambiarlo a un calendario.
from django.urls import reverse # Asegúrate que esta importación esté al inicio del archivo si no está ya
from django.utils.html import format_html
# from django.http import JsonResponse # Movido a admin_views.py
# from django.utils import timezone # Movido a admin_views.py
# from datetime import datetime, timedelta # Movido a admin_views.py
from .utils import check_and_cancel_expired_appointments, send_appointment_confirmation_email, send_invoice_generated_email
@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'client', 'get_client_full_name', 'get_client_address', 
        'service', 'get_client_phone', 'appointment_date', 
        'appointment_time', 'status', 'created_at', 'generate_invoice_button',
    )
    list_filter = ('status', 'appointment_date', 'service', 'staff', 'created_at')
    search_fields = (
        'client__username', 'client__first_name', 'client__last_name', 'client__email',
        'service__name', 'staff__username', 'staff__first_name', 'staff__last_name'
    )
    date_hierarchy = 'appointment_date'
    raw_id_fields = ('client', 'service', 'staff')
    readonly_fields = ('created_at',)
    list_display_links = ('id', 'client')
    list_per_page = 25
    
    # --- NUEVO: Botón Manual en el menú de acciones ---
    actions = ['action_clean_expired_appointments']

    fieldsets = (
        (_('Información Principal'), {
            'fields': ('client', 'service', 'status')
        }),
        (_('Fecha y Hora'), {
            'fields': ('appointment_date', 'appointment_time')
        }),
        (_('Asignación y Notas'), {
            'fields': ('staff', 'notes')
        }),
        (_('Metadata'), {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )

    # --- 1. ESTO HACE QUE SE ACTUALICE AL REFRESCAR LA PÁGINA ---
    def changelist_view(self, request, extra_context=None):
        from .utils import check_and_cancel_expired_appointments
        
        # Ejecutamos la limpieza y pasamos 'request' para ver mensajes
        cancelled = check_and_cancel_expired_appointments(request)
        
        return super().changelist_view(request, extra_context=extra_context)
    # -----------------------------------------------------------

    # --- 2. ESTO AGREGA EL BOTÓN MANUAL EN "ACCIONES" ---
    def action_clean_expired_appointments(self, request, queryset):
        from .utils import check_and_cancel_expired_appointments
        from django.contrib import messages
        
        # Ejecutamos la limpieza forzada
        cancelled = check_and_cancel_expired_appointments(request)
        
        if cancelled == 0:
            self.message_user(request, "El sistema está al día. No se encontraron citas vencidas.", level=messages.INFO)
        else:
            self.message_user(request, f"Limpieza completada: Se cancelaron {cancelled} citas vencidas.", level=messages.SUCCESS)
            
    action_clean_expired_appointments.short_description = "Verificar y Cancelar citas vencidas (Regla 24h)"
    # ----------------------------------------------------

    def get_client_full_name(self, obj):
        if obj.client:
            return obj.client.get_full_name() or obj.client.username
        return "N/A"
    get_client_full_name.short_description = _('Nombre')

    def get_client_address(self, obj):
        if obj.client:
            address = getattr(obj.client, 'address', None)
            if address and address != 'N/A' and address.strip():
                # Codificamos la dirección para URL (espacios -> %20, etc.)
                encoded_address = quote(address)
                google_maps_url = f"https://www.google.com/maps/search/?api=1&query={encoded_address}"
                
                # Retornamos el link azulito (#007bff) que abre en nueva pestaña
                return format_html(
                    '<a href="{}" target="_blank" style="color: #007bff; font-weight: bold;">'
                    '<i class="fas fa-map-marker-alt"></i> {}'
                    '</a>',
                    google_maps_url,
                    address
                )
            return getattr(obj.client, 'address', 'N/A')
        return "N/A"
    get_client_address.short_description = _('Dirección (Ver Mapa)')

    def get_client_phone(self, obj):
        if obj.client:
            return getattr(obj.client, 'phone_number', 'N/A')
        return "N/A"
    get_client_phone.short_description = 'Teléfono del Cliente'

    def get_urls(self):
        from django.urls import path
        urls = super().get_urls()
        
        info = self.model._meta.app_label, self.model._meta.model_name
        stats_api_url_name = '%s_%s_stats_api' % info
        generate_invoice_url_name = '%s_%s_generate_invoice' % info

        custom_urls = [
            path('stats/api/', 
                 self.admin_site.admin_view(self.appointments_stats_api_local),
                 name=stats_api_url_name),
            path('<int:appointment_id>/generate_invoice/', 
                 self.admin_site.admin_view(self.generate_invoice_view),
                 name=generate_invoice_url_name),
        ]
        return custom_urls + urls

    def appointments_stats_api_local(self, request):
        from django.http import JsonResponse
        from django.utils import timezone
        from datetime import timedelta
        
        end_date = timezone.now()
        start_date = end_date - timedelta(days=30)
        appointments = self.model.objects.filter(created_at__range=[start_date, end_date])
        dates = []
        confirmed = []
        pending = []
        completed = []
        current_date_iter = start_date
        while current_date_iter <= end_date:
            dates.append(current_date_iter.date().isoformat())
            day_appointments = appointments.filter(created_at__date=current_date_iter.date())
            confirmed.append(day_appointments.filter(status='confirmed').count())
            pending.append(day_appointments.filter(status='pending').count())
            completed.append(day_appointments.filter(status='completed').count())
            current_date_iter += timedelta(days=1)
        return JsonResponse({
            'dates': dates, 'confirmed': confirmed, 'pending': pending, 'completed': completed,
        })

    def generate_invoice_button(self, obj):
        from django.urls import reverse
        from django.utils.html import format_html
        
        info = self.model._meta.app_label, self.model._meta.model_name
        generate_invoice_url_name = '%s_%s_generate_invoice' % info
        
        # Detectar tipo de comprobante sugerido
        has_ruc = getattr(obj.client, 'ruc', None)
        doc_type = "Factura" if has_ruc else "Boleta"
        
        if obj.status == 'pending':
            return format_html(
                '<a href="{}" class="button" style="background-color: #28a745; color: white;">'
                '<i class="fas fa-file-invoice"></i> Generar {}</a>',
                reverse(f'admin:{generate_invoice_url_name}', args=[obj.pk]),
                doc_type
            )
        elif obj.status in ['confirmed', 'completed']:
            try:
                from invoices.models import Invoice
                invoice = Invoice.objects.filter(appointment=obj).latest('created_at')
                # Determinar color según estado
                color = "#28a745" if invoice.status == 'pagada' else "#007bff"
                return format_html(
                    '<a href="{}" class="button" style="background-color: {}; color: white;">'
                    '<i class="fas fa-file-invoice"></i> Ver {} #{}</a>',
                    reverse('admin:invoices_invoice_change', args=[invoice.pk]),
                    color,
                    invoice.get_invoice_type_display(), # Muestra "Factura" o "Boleta"
                    invoice.number or "(borrador)"
                )
            except Exception:
                return format_html(
                    '<a href="{}" class="button" style="background-color: #17a2b8; color: white;">'
                    '<i class="fas fa-file-invoice"></i> Nueva {}</a>',
                    reverse(f'admin:{generate_invoice_url_name}', args=[obj.pk]),
                    doc_type
                )
        return "-"
    generate_invoice_button.short_description = "Comprobante"

    def generate_invoice_view(self, request, appointment_id):
        from invoices.models import Invoice, InvoiceItem
        from decimal import Decimal
        from django.utils import timezone
        from django.contrib import messages
        
        appointment = get_object_or_404(Appointment, id=appointment_id)
        existing = Invoice.objects.filter(appointment=appointment).first()
        
        if existing:
            self.message_user(request, f"La cita ya tiene un comprobante asociado.", level=messages.INFO)
            return redirect('admin:invoices_invoice_change', existing.id)
        
        # --- LÓGICA DE FACTURA VS BOLETA ---
        client = appointment.client
        # Verificamos si tiene RUC (asumiendo que guardaste el RUC en el modelo User)
        has_ruc = getattr(client, 'ruc', None) and len(str(client.ruc).strip()) == 11
        
        if has_ruc:
            doc_type = 'factura'
            series = 'F001' # Serie estándar para Facturas electrónicas
        else:
            doc_type = 'boleta'
            series = 'B001' # Serie estándar para Boletas electrónicas
            
        invoice = Invoice(
            invoice_type=doc_type,
            series=series,
            client=client, 
            status='borrador',
            created_by=request.user, 
            notes=f"Generado autom. desde cita #{appointment.id}",
            date_issued=timezone.now(), 
            payment_method='efectivo'
        )
        
        try:
            invoice.save()
            invoice.appointment = appointment
            invoice.save()
            
            # Obtener precio del servicio
            price_val = getattr(appointment.service, 'base_price', getattr(appointment.service, 'price', 0))
            price = Decimal(str(price_val)) if price_val else Decimal('0.00')

            # Crear el item
            InvoiceItem.objects.create(
                invoice=invoice, 
                item_type='service', 
                service=appointment.service,
                description=appointment.service.name, 
                quantity=1, 
                unit_price=price,
                subtotal=price
            )
            
            # Recalcular totales (esto llama al save del modelo Invoice que ya tiene la lógica)
            invoice.save()
            send_invoice_generated_email(request, invoice)
            msg_type = "Factura" if has_ruc else "Boleta"
            self.message_user(request, f"{msg_type} creada correctamente.")
            return redirect('admin:invoices_invoice_change', invoice.id)
            
        except Exception as e:
            self.message_user(request, f"Error al generar comprobante: {e}", level=messages.ERROR)
            return redirect(f'admin:{self.model._meta.app_label}_{self.model._meta.model_name}_changelist')
        
    def save_model(self, request, obj, form, change):
        if change:
            old_obj = Appointment.objects.get(pk=obj.pk)
            # Si cambia a confirmado
            if old_obj.status != 'confirmed' and obj.status == 'confirmed':
                # ---> AQUÍ: Pasamos 'request'
                send_appointment_confirmation_email(request, obj)
                self.message_user(request, f"Correo de confirmación enviado a {obj.client.email}", level=messages.SUCCESS)
        
        super().save_model(request, obj, form, change)    
from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from .models import Appointment, WorkScheduleTemplate, ScheduledWorkDay
from django.contrib import messages 
from django.shortcuts import get_object_or_404, redirect
from urllib.parse import quote
from services.models import Service 
from django.contrib.auth import get_user_model
from django.urls import reverse 
from django.utils.html import format_html
# Quitamos las importaciones de envio de correo de aquí, ya no se usan en esta vista
from .utils import check_and_cancel_expired_appointments 

User = get_user_model() 

# --- Admin para Modelos de Horario ---

@admin.register(WorkScheduleTemplate)
class WorkScheduleTemplateAdmin(admin.ModelAdmin):
    list_display = ('get_day_of_week_display', 'start_time', 'end_time', 'is_working_day')
    list_editable = ('start_time', 'end_time', 'is_working_day')
    ordering = ('day_of_week',)

    def get_day_of_week_display(self, obj):
        return obj.get_day_of_week_display()
    get_day_of_week_display.short_description = _('Día de la semana')

# --- MODIFICACIÓN EN ScheduledWorkDayAdmin ---
@admin.register(ScheduledWorkDay)
class ScheduledWorkDayAdmin(admin.ModelAdmin):
    change_list_template = 'admin/appointments/calendar.html'

    def changelist_view(self, request, extra_context=None):
        cancelled = check_and_cancel_expired_appointments(request)
        if cancelled > 0:
            messages.warning(request, f"MANTENIMIENTO: Se han cancelado {cancelled} citas vencidas automáticamente.")
        return super().changelist_view(request, extra_context=extra_context)

# --- Admin para Citas ---
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

    def changelist_view(self, request, extra_context=None):
        cancelled = check_and_cancel_expired_appointments(request)
        return super().changelist_view(request, extra_context=extra_context)

    def action_clean_expired_appointments(self, request, queryset):
        cancelled = check_and_cancel_expired_appointments(request)
        if cancelled == 0:
            self.message_user(request, "El sistema está al día. No se encontraron citas vencidas.", level=messages.INFO)
        else:
            self.message_user(request, f"Limpieza completada: Se cancelaron {cancelled} citas vencidas.", level=messages.SUCCESS)
            
    action_clean_expired_appointments.short_description = "Verificar y Cancelar citas vencidas (Regla 24h)"

    def get_client_full_name(self, obj):
        if obj.client:
            return obj.client.get_full_name() or obj.client.username
        return "N/A"
    get_client_full_name.short_description = _('Nombre')
    
    def get_client_address(self, obj):
        if obj.client:
            address = getattr(obj.client, 'address', None)
            if address and address != 'N/A' and address.strip():
                encoded_address = quote(address)
                google_maps_url = f"https://www.google.com/maps/search/?api=1&query={encoded_address}"
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
                color = "#28a745" if invoice.status == 'pagada' else "#007bff"
                return format_html(
                    '<a href="{}" class="button" style="background-color: {}; color: white;">'
                    '<i class="fas fa-file-invoice"></i> Ver {} #{}</a>',
                    reverse('admin:invoices_invoice_change', args=[invoice.pk]),
                    color,
                    invoice.get_invoice_type_display(),
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
        
        appointment = get_object_or_404(Appointment, id=appointment_id)
        existing = Invoice.objects.filter(appointment=appointment).first()
        
        if existing:
            self.message_user(request, f"La cita ya tiene un comprobante asociado.", level=messages.INFO)
            return redirect('admin:invoices_invoice_change', existing.id)
        
        # Lógica de Factura vs Boleta
        client = appointment.client
        has_ruc = getattr(client, 'ruc', None) and len(str(client.ruc).strip()) == 11
        
        if has_ruc:
            doc_type = 'factura'
            series = 'F001'
        else:
            doc_type = 'boleta'
            series = 'B001'
            
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
            
            price_val = getattr(appointment.service, 'base_price', getattr(appointment.service, 'price', 0))
            price = Decimal(str(price_val)) if price_val else Decimal('0.00')

            InvoiceItem.objects.create(
                invoice=invoice, 
                item_type='service', 
                service=appointment.service,
                description=appointment.service.name, 
                quantity=1, 
                unit_price=price,
                subtotal=price
            )
            
            invoice.save()
            
            # --- AQUÍ ESTÁ EL CAMBIO: YA NO ENVIAMOS CORREO AHORA ---
            # Solo avisamos al admin que se creó el borrador.
            
            msg_type = "Factura" if has_ruc else "Boleta"
            self.message_user(request, f"{msg_type} generada en Borrador. Ingrese el adelanto (mín. 50 soles) y guarde para confirmar la cita.", level=messages.SUCCESS)
            return redirect('admin:invoices_invoice_change', invoice.id)
            
        except Exception as e:
            self.message_user(request, f"Error al generar comprobante: {e}", level=messages.ERROR)
            return redirect(f'admin:{self.model._meta.app_label}_{self.model._meta.model_name}_changelist')
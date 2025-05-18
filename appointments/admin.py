# appointments/admin.py
from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from .models import Appointment, WorkScheduleTemplate, ScheduledWorkDay
from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect
# --- Admin para Modelos de Horario ---

@admin.register(WorkScheduleTemplate)
class WorkScheduleTemplateAdmin(admin.ModelAdmin):
    list_display = ('get_day_of_week_display', 'start_time', 'end_time', 'is_working_day')
    list_editable = ('start_time', 'end_time', 'is_working_day')
    ordering = ('day_of_week',)

    def get_day_of_week_display(self, obj):
        return obj.get_day_of_week_display()
    get_day_of_week_display.short_description = _('Día de la semana')

@admin.register(ScheduledWorkDay)
class ScheduledWorkDayAdmin(admin.ModelAdmin):
    list_display = ('date', 'get_day_name', 'start_time', 'end_time', 'is_working', 'notes')
    list_filter = ('is_working', 'date')
    search_fields = ('date', 'notes')
    date_hierarchy = 'date'
    ordering = ('date',)
    list_editable = ('start_time', 'end_time', 'is_working', 'notes')

    def get_day_name(self, obj):
        days = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
        return days[obj.date.weekday()]
    get_day_name.short_description = _('Día')


# --- Admin para Citas (Modificado) ---
from django.urls import reverse
from django.utils.html import format_html

from django.http import JsonResponse
from django.utils import timezone
from datetime import datetime, timedelta
from django.contrib.auth.decorators import login_required
@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'client', # Cambiado a client
        'get_client_full_name', # Añadido para mostrar el nombre completo
        'get_client_address', # Añadido para mostrar la dirección
        'service',
        'get_client_phone', # Añadido para mostrar el teléfono
        'appointment_date', # Añadido
        'appointment_time', # Añadido
        'status',
        'created_at',
        'generate_invoice_button',
    )
    list_filter = ('status', 'appointment_date', 'service', 'staff', 'created_at') # Añadido staff y appointment_date
    search_fields = (
        'client__username', 'client__first_name', 'client__last_name', 'client__email', # Buscar por cliente
        'service__name', # Buscar por servicio
        'staff__username', 'staff__first_name', 'staff__last_name' # Buscar por staff
    )
    date_hierarchy = 'appointment_date' # Jerarquía por fecha de cita
    # Usar raw_id_fields para mejor rendimiento con muchos usuarios/servicios/staff
    raw_id_fields = ('client', 'service', 'staff')
    readonly_fields = ('created_at',) # Campos que no se editan en el admin
    list_display_links = ('id', 'client') # Campos que linkean al detalle
    list_per_page = 25 # Paginación

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
            'classes': ('collapse',) # Ocultar por defecto
        }),
    )

    def get_client_full_name(self, obj):
        return obj.client.get_full_name() or obj.client.username
    get_client_full_name.short_description = _('Nombre')
    
    def get_client_address(self, obj):
        return obj.client.address
    get_client_address.short_description = _('Dirección del Cliente')

    def get_client_phone(self, obj):
        return obj.client.phone_number  # Asegúrate de que 'client' tiene el campo 'phone_number'
    get_client_phone.short_description = 'Teléfono del Cliente'

    def get_urls(self):
        from django.urls import path
        urls = super().get_urls()
        custom_urls = [
            path('stats/api/', self.admin_site.admin_view(self.appointments_stats_api), 
                 name='appointments_stats_api'),
        ]

        return custom_urls + urls

           
    def appointments_stats_api(self, request):
        # Calculate stats for last 30 days
        end_date = timezone.now()
        start_date = end_date - timedelta(days=30)
        
        # Get appointments in date range
        appointments = Appointment.objects.filter(
            created_at__range=[start_date, end_date]
        )
        
        # Initialize data arrays
        dates = []
        confirmed = []
        pending = []
        completed = []
        
        # Generate data for each day
        current_date = start_date
        while current_date <= end_date:
            dates.append(current_date.date().isoformat())
            day_appointments = appointments.filter(created_at__date=current_date.date())
            
            confirmed.append(day_appointments.filter(status='confirmed').count())
            pending.append(day_appointments.filter(status='pending').count())
            completed.append(day_appointments.filter(status='completed').count())
            
            current_date += timedelta(days=1)
        return JsonResponse({
            'dates': dates,
            'confirmed': confirmed,
            'pending': pending,
            'completed': completed,
        })
    
    def generate_invoice_button(self, obj):
        """Añade un botón para generar boleta desde la cita"""
        if obj.status == 'pending':
            return format_html(
                '<a href="{}" class="button" style="background-color: #28a745; color: white;">'
                '<i class="fas fa-file-invoice"></i> Generar Boleta</a>',
                reverse('admin:generate_invoice_from_appointment', args=[obj.pk])
            )
        elif obj.status in ['confirmed', 'completed']:
            # Intentar encontrar la boleta asociada
            from invoices.models import Invoice
            try:
                invoice = Invoice.objects.filter(
                    appointment=obj, 
                    status__in=['borrador', 'emitida', 'pagada']
                ).latest('created_at')
                return format_html(
                    '<a href="{}" class="button" style="background-color: #007bff; color: white;">'
                    '<i class="fas fa-file-invoice"></i> Ver Boleta #{}</a>',
                    reverse('admin:invoices_invoice_change', args=[invoice.pk]),
                    invoice.number or "(borrador)"
                )
            except Invoice.DoesNotExist:
                return format_html(
                    '<a href="{}" class="button" style="background-color: #17a2b8; color: white;">'
                    '<i class="fas fa-file-invoice"></i> Nueva Boleta</a>',
                    reverse('admin:generate_invoice_from_appointment', args=[obj.pk])
                )
        return "-"
    
    generate_invoice_button.short_description = "Boleta"
    generate_invoice_button.allow_tags = True

    def get_urls(self):
        from django.urls import path
        urls = super().get_urls()
        custom_urls = [
            path('stats/api/', self.admin_site.admin_view(self.appointments_stats_api), 
                 name='appointments_stats_api'),
            path('<int:appointment_id>/generate_invoice/', 
                 self.admin_site.admin_view(self.generate_invoice_view),
                 name='generate_invoice_from_appointment'),
        ]
        return custom_urls + urls
    
        
    def generate_invoice_view(self, request, appointment_id):
        """Vista para generar una boleta desde una cita"""
        appointment = get_object_or_404(Appointment, id=appointment_id)
    
    # Si la cita ya tiene una boleta, redirigir a ella
        from invoices.models import Invoice
        existing_invoice = Invoice.objects.filter(appointment=appointment).first()
        if existing_invoice:
            self.message_user(request, 
                            f"La cita ya tiene una boleta asociada (#{existing_invoice.number or '(borrador)'})", 
                            level=messages.INFO)
            return redirect('admin:invoices_invoice_change', existing_invoice.id)
    
    # Crear la factura sin asignar appointment primero
        from django.utils import timezone
        invoice = Invoice(
            invoice_type='boleta',
            client=appointment.client,
            status='borrador',
            created_by=request.user,
            notes=f"Boleta generada desde cita #{appointment.id}",
            date_issued=timezone.now(),
        # Por defecto efectivo
            payment_method='efectivo',
        )
    
    # Guardar primero para obtener un ID
        try:
            invoice.save()
        
        # Ahora que la factura tiene un ID, establecer la relación y guardar de nuevo
            invoice.appointment = appointment
            invoice.save()
        
        # Añadir el servicio como ítem
            from invoices.models import InvoiceItem
            from decimal import Decimal
        
        # Obtener el precio base del servicio
            service_price = getattr(appointment.service, 'base_price', 0)
            if not service_price:
                service_price = getattr(appointment.service, 'price', 0)
        
            item = InvoiceItem.objects.create(
                invoice=invoice,
                item_type='service',
                service=appointment.service,
                description=appointment.service.name,
                quantity=1,
                unit_price=service_price,
                discount=0,
                subtotal=service_price
        )
        
        # Actualizar los totales manualmente
            invoice.subtotal = service_price
            invoice.igv = invoice.subtotal * Decimal('0.18')
            invoice.total = invoice.subtotal + invoice.igv
            invoice.pending_balance = invoice.total - invoice.advance_payment
            invoice.save()
        
        # Mostrar mensaje de éxito
            self.message_user(request, "Boleta creada correctamente. Complete los detalles y guarde.")
        
        # Redireccionar al formulario de la boleta
            return redirect('admin:invoices_invoice_change', invoice.id)
        
        except Exception as e:
            self.message_user(request, f"Error al crear la boleta: {str(e)}", level=messages.ERROR)
            return redirect('admin:appointments_appointment_changelist')


    # Ya no se necesitan los métodos get_appointment_date/time
    # porque los campos están directamente en el modelo.


    
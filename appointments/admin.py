# appointments/admin.py
from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from .models import Appointment, WorkScheduleTemplate, ScheduledWorkDay
from django.contrib import messages # No se usa directamente en el admin modificado, pero está bien tenerla
from django.shortcuts import get_object_or_404, redirect # No se usa directamente, pero está bien tenerla

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

# --- MODIFICACIÓN AQUÍ para ScheduledWorkDayAdmin ---
@admin.register(ScheduledWorkDay)
class ScheduledWorkDayAdmin(admin.ModelAdmin):
    # Ya no mostraremos la lista de tabla estándar, así que list_display, list_filter, etc.,
    # no tendrán efecto directo en la vista del calendario, pero pueden ser útiles
    # si accedes a la vista de alguna otra forma o para la estructura interna del admin.
    # list_display = ('date', 'get_day_name', 'start_time', 'end_time', 'is_working', 'notes')
    # list_filter = ('is_working', 'date')
    # search_fields = ('date', 'notes')
    # date_hierarchy = 'date'
    # ordering = ('date',)
    # list_editable = ('start_time', 'end_time', 'is_working', 'notes')

    # 1. Especificamos nuestra plantilla de calendario personalizada
    change_list_template = 'admin/appointments/calendar.html'

    # 2. Sobrescribimos changelist_view para pasar el contexto necesario a la plantilla
    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        
        # Título para la página del calendario
        extra_context['title'] = _('Calendario de Días Programados y Citas')
        
        # Estos son para los filtros desplegables en calendar.html.
        # La API `calendar_events_api` los usa para filtrar las *citas* que se muestran.
        # Los `ScheduledWorkDay` se mostrarán siempre como eventos de fondo.
        # Si no quieres mostrar citas o estos filtros en esta vista específica,
        # podrías omitir pasar 'services' y 'staff_members' y quitar los filtros del HTML.
        try:
            extra_context['services'] = Service.objects.all()
        except Exception as e: # Captura por si el modelo Service no está listo o hay otro error
            extra_context['services'] = []
            messages.warning(request, f"No se pudieron cargar los servicios para los filtros: {e}")

        try:
            extra_context['staff_members'] = User.objects.filter(is_staff=True)
        except Exception as e: # Captura por si el modelo User tiene algún problema
            extra_context['staff_members'] = []
            messages.warning(request, f"No se pudieron cargar los miembros del personal para los filtros: {e}")
            
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

@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'client', 
        'get_client_full_name', 
        'get_client_address', 
        'service',
        'get_client_phone', 
        'appointment_date', 
        'appointment_time', 
        'status',
        'created_at',
        'generate_invoice_button', # Tu botón personalizado
    )
    list_filter = ('status', 'appointment_date', 'service', 'staff', 'created_at')
    search_fields = (
        'client__username', 'client__first_name', 'client__last_name', 'client__email',
        'service__name', 
        'staff__username', 'staff__first_name', 'staff__last_name'
    )
    date_hierarchy = 'appointment_date'
    raw_id_fields = ('client', 'service', 'staff')
    readonly_fields = ('created_at',)
    list_display_links = ('id', 'client')
    list_per_page = 25

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

    def get_client_full_name(self, obj):
        # Es buena práctica verificar si client existe antes de acceder a sus atributos
        if obj.client:
            return obj.client.get_full_name() or obj.client.username
        return "N/A"
    get_client_full_name.short_description = _('Nombre')
    
    def get_client_address(self, obj):
        if obj.client:
            return getattr(obj.client, 'address', 'N/A') # Usar getattr para seguridad
        return "N/A"
    get_client_address.short_description = _('Dirección del Cliente')

    def get_client_phone(self, obj):
        if obj.client:
            return getattr(obj.client, 'phone_number', 'N/A') # Usar getattr
        return "N/A"
    get_client_phone.short_description = 'Teléfono del Cliente'

    # ----- IMPORTANTE: Corrección de get_urls duplicado -----
    # Tenías dos definiciones de get_urls. Aquí está la versión fusionada
    # que incluye tanto tu API de estadísticas como la generación de boletas.
    def get_urls(self):
        from django.urls import path
        from django.utils import timezone # Necesario para appointments_stats_api
        from datetime import timedelta  # Necesario para appointments_stats_api
        from django.http import JsonResponse # Necesario para appointments_stats_api

        urls = super().get_urls()
        
        # Define un nombre único para la URL de la API de estadísticas interna del ModelAdmin
        # para evitar conflictos.
        info = self.model._meta.app_label, self.model._meta.model_name
        stats_api_url_name = '%s_%s_stats_api' % info
        generate_invoice_url_name = '%s_%s_generate_invoice' % info


        custom_urls = [
            path('stats/api/', 
                 self.admin_site.admin_view(self.appointments_stats_api_local), # Renombrar para evitar confusión
                 name=stats_api_url_name),
            path('<int:appointment_id>/generate_invoice/', 
                 self.admin_site.admin_view(self.generate_invoice_view),
                 name=generate_invoice_url_name),
        ]
        return custom_urls + urls
    
    # Renombrado para evitar conflicto con la API global de admin_views.py
    def appointments_stats_api_local(self, request): 
        # ... (tu código existente para appointments_stats_api) ...
        # Para brevedad, no lo repito aquí, pero asegúrate que esté completo
        # y que use timezone, timedelta, JsonResponse que deben importarse dentro de get_urls o globalmente.
        # Este es el código que tenías:
        end_date = timezone.now()
        start_date = end_date - timedelta(days=30)
        appointments = Appointment.objects.filter(created_at__range=[start_date, end_date])
        dates = []
        confirmed = []
        pending = []
        completed = []
        current_date_iter = start_date # Renombrar variable para evitar conflicto con el módulo datetime
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
        # Usa el nombre de URL corregido y con namespace 'admin:'
        # Asume que el nombre de la URL para generar boleta es 'admin:appointments_appointment_generate_invoice'
        # Esto dependerá de cómo registres las URLs del ModelAdmin.
        # Por ahora, usando el nombre que generamos en get_urls.
        info = self.model._meta.app_label, self.model._meta.model_name
        generate_invoice_url_name = '%s_%s_generate_invoice' % info
        
        if obj.status == 'pending':
            return format_html(
                '<a href="{}" class="button" style="background-color: #28a745; color: white;">'
                '<i class="fas fa-file-invoice"></i> Generar Boleta</a>',
                reverse(f'admin:{generate_invoice_url_name}', args=[obj.pk])
            )
        elif obj.status in ['confirmed', 'completed']:
            from invoices.models import Invoice # Importación local
            try:
                invoice = Invoice.objects.filter(
                    appointment=obj, 
                    status__in=['borrador', 'emitida', 'pagada']
                ).latest('created_at')
                return format_html(
                    '<a href="{}" class="button" style="background-color: #007bff; color: white;">'
                    '<i class="fas fa-file-invoice"></i> Ver Boleta #{}</a>',
                    reverse('admin:invoices_invoice_change', args=[invoice.pk]), # Asume que tienes un admin para Invoice en la app 'invoices'
                    invoice.number or "(borrador)"
                )
            except Invoice.DoesNotExist:
                return format_html(
                    '<a href="{}" class="button" style="background-color: #17a2b8; color: white;">'
                    '<i class="fas fa-file-invoice"></i> Nueva Boleta</a>',
                    reverse(f'admin:{generate_invoice_url_name}', args=[obj.pk])
                )
        return "-"
    generate_invoice_button.short_description = "Boleta"
    # generate_invoice_button.allow_tags = True # allow_tags está obsoleto en Django >= 4.0. format_html ya es seguro.

    def generate_invoice_view(self, request, appointment_id):
        # ... (tu código existente para generate_invoice_view) ...
        # Asegúrate que las importaciones necesarias (Invoice, InvoiceItem, Decimal, timezone) estén disponibles.
        # Para brevedad, no lo repito aquí.
        # Ejemplo de una importación necesaria:
        from invoices.models import Invoice, InvoiceItem
        from decimal import Decimal
        from django.utils import timezone # Ya debería estar importada globalmente o dentro de get_urls

        appointment = get_object_or_404(Appointment, id=appointment_id)
        existing_invoice = Invoice.objects.filter(appointment=appointment).first()
        if existing_invoice:
            self.message_user(request, f"La cita ya tiene una boleta asociada (#{existing_invoice.number or '(borrador)'})", level=messages.INFO)
            return redirect('admin:invoices_invoice_change', existing_invoice.id) # Asume esta URL name
        
        invoice = Invoice(
            invoice_type='boleta', client=appointment.client, status='borrador',
            created_by=request.user, notes=f"Boleta generada desde cita #{appointment.id}",
            date_issued=timezone.now(), payment_method='efectivo'
        )
        try:
            invoice.save()
            invoice.appointment = appointment
            invoice.save()
            
            service_price_attr = getattr(appointment.service, 'base_price', None)
            if service_price_attr is None: # Si no hay base_price, intenta con price
                 service_price_attr = getattr(appointment.service, 'price', 0)
            
            service_price = Decimal(str(service_price_attr)) if service_price_attr is not None else Decimal('0.00')


            InvoiceItem.objects.create(
                invoice=invoice, item_type='service', service=appointment.service,
                description=appointment.service.name, quantity=1, unit_price=service_price,
                discount=0, subtotal=service_price
            )
            invoice.subtotal = service_price
            invoice.igv = invoice.subtotal * Decimal('0.18') # Asegúrate que Decimal esté importado
            invoice.total = invoice.subtotal + invoice.igv
            invoice.pending_balance = invoice.total - getattr(invoice, 'advance_payment', Decimal('0.00')) # Usa getattr por si advance_payment no existe o es None
            invoice.save()
            self.message_user(request, "Boleta creada. Complete detalles y guarde.")
            return redirect('admin:invoices_invoice_change', invoice.id) # Asume esta URL name
        except Exception as e:
            self.message_user(request, f"Error al crear la boleta: {str(e)}", level=messages.ERROR)
            return redirect(f'admin:{self.model._meta.app_label}_{self.model._meta.model_name}_changelist')
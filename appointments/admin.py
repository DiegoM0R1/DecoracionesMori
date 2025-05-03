# appointments/admin.py
from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from .models import Appointment, WorkScheduleTemplate, ScheduledWorkDay

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

@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'client',
        'service',
        'staff', # Añadido
        'appointment_date', # Añadido
        'appointment_time', # Añadido
        'status',
        'created_at'
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

    # Ya no se necesitan los métodos get_appointment_date/time
    # porque los campos están directamente en el modelo.
from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from .models import StaffAvailability, Appointment

@admin.register(StaffAvailability)
class StaffAvailabilityAdmin(admin.ModelAdmin):
    list_display = ('staff', 'date', 'start_time', 'end_time', 'is_available')
    list_filter = ('is_available', 'date', 'staff')
    search_fields = ('staff__username', 'staff__first_name', 'staff__last_name')
    date_hierarchy = 'date'

@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = ('client', 'service', 'get_appointment_date', 'get_appointment_time', 'status', 'created_at')
    list_filter = ('status', 'service', 'created_at')
    search_fields = ('client__username', 'client__first_name', 'client__last_name', 'service__name')
    date_hierarchy = 'created_at'
    raw_id_fields = ('client', 'service', 'staff_availability')
    readonly_fields = ('created_at',)
    
    def get_appointment_date(self, obj):
        if obj.staff_availability:
            return obj.staff_availability.date
        return "-"
    get_appointment_date.short_description = _("Date")
    
    def get_appointment_time(self, obj):
        if obj.staff_availability:
            return f"{obj.staff_availability.start_time} - {obj.staff_availability.end_time}"
        return "-"
    get_appointment_time.short_description = _("Time")
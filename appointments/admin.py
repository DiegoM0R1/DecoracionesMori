from django.contrib import admin
from .models import Appointment, StaffAvailability

@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = ('client', 'service', 'staff_availability', 'created_at', 'status')
    list_filter = ('status', 'created_at')
    search_fields = ('client__username', 'service__name')

@admin.register(StaffAvailability)
class StaffAvailabilityAdmin(admin.ModelAdmin):
    list_display = ('staff', 'date', 'start_time', 'end_time', 'is_available')
    list_filter = ('is_available', 'date')
    search_fields = ('staff__username',)
    
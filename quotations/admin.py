from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from .models import Quotation, QuotationItem

class QuotationItemInline(admin.TabularInline):
    model = QuotationItem
    extra = 1
    raw_id_fields = ('service', 'product')

@admin.register(Quotation)
class QuotationAdmin(admin.ModelAdmin):
    list_display = ('quotation_number', 'client', 'get_appointment_date', 'total_amount', 'status', 'created_at', 'valid_until')
    list_filter = ('status', 'created_at')
    search_fields = ('quotation_number', 'client__username', 'client__first_name', 'client__last_name')
    date_hierarchy = 'created_at'
    readonly_fields = ('quotation_number', 'created_at', 'updated_at')
    raw_id_fields = ('client', 'appointment', 'staff')
    inlines = [QuotationItemInline]
    
    def get_appointment_date(self, obj):
        if obj.appointment and obj.appointment.staff_availability:
            return obj.appointment.staff_availability.date
        return "-"
    get_appointment_date.short_description = _("Appointment Date")
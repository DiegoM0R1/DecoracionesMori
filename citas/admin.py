from django.contrib import admin

# Register your models here.
from django.contrib import admin
from .models import Quotation, QuotationItem
from django.utils.translation import gettext_lazy as _

class QuotationItemInline(admin.TabularInline):
    model = QuotationItem
    extra = 1
    fields = ('item_type', 'service', 'product', 'description', 'quantity', 'unit_price', 'total_price')
    readonly_fields = ('total_price',)

@admin.register(Quotation)
class QuotationAdmin(admin.ModelAdmin):
    list_display = ('quotation_number', 'client', 'staff', 'created_at', 'total_amount', 'status')
    list_filter = ('status', 'created_at')
    search_fields = ('quotation_number', 'client__username', 'client__email')
    inlines = [QuotationItemInline]
    readonly_fields = ('quotation_number', 'total_amount')
    fieldsets = (
        (None, {
            'fields': ('client', 'appointment', 'staff', 'quotation_number')
        }),
        (_('Quotation Details'), {
            'fields': ('valid_until', 'status', 'total_amount', 'notes')
        }),
    )
    
    def save_formset(self, request, form, formset, change):
        instances = formset.save(commit=False)
        for instance in instances:
            if instance.item_type == 'service' and instance.service:
                instance.description = instance.service.name
                if not instance.unit_price:
                    instance.unit_price = instance.service.base_price
            elif instance.item_type == 'product' and instance.product:
                instance.description = instance.product.name
                if not instance.unit_price:
                    instance.unit_price = instance.product.price_per_unit
            
            instance.save()
        
        # Also delete objects marked for deletion
        for obj in formset.deleted_objects:
            obj.delete()
        
        # Update quotation total
        quotation = form.instance
        total = sum(item.total_price for item in quotation.items.all())
        quotation.total_amount = total
        quotation.save()
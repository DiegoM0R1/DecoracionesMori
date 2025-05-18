# clients/admin.py
from django.contrib import admin
from .models import ClientProfile

class ClientProfileAdmin(admin.ModelAdmin):
    list_display = ['client_type', 'get_full_name', 'get_email', 'get_phone', 'get_address']
    list_filter = ['client_type']
    search_fields = ['user__username', 'user__email', 'user__first_name', 'user__last_name', 'user__phone_number','user__address']
    
    def get_full_name(self, obj):
        return obj.user.get_full_name() or obj.user.username
    get_full_name.short_description = 'Nombre Completo'
    
    def get_email(self, obj):
        return obj.user.email
    get_email.short_description = 'Email'
    
    def get_phone(self, obj):
        return obj.user.phone_number
    get_phone.short_description = 'Teléfono'
    def get_address(self, obj):
        return obj.user.address
    get_address.short_description = 'Dirección'
    # El método get_registration_date parece que no está definido
    # Puedes añadirlo si necesitas la fecha de registro:
    def get_registration_date(self, obj):
        return obj.user.date_joined
    get_registration_date.short_description = 'Fecha de Registro'
    
    # Si quieres modificar los campos en el formulario de edición:
    fieldsets = (
        (None, {
            'fields': ('user', 'client_type')
        }),
    )
    
    # Para el formulario de añadir un nuevo ClientProfile
    add_fieldsets = (
        (None, {
            'fields': ('user', 'client_type')
        }),
    )

admin.site.register(ClientProfile, ClientProfileAdmin)
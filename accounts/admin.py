from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User
from allauth.socialaccount.models import SocialApp, SocialAccount
from allauth.socialaccount.admin import SocialAppAdmin as BaseSocialAppAdmin, SocialAccountAdmin

class CustomUserAdmin(UserAdmin):
    """
    Configuración del modelo de usuario en el panel de administración
    """
    list_display = (
        'username', 
        'email', 
        'first_name', 
        'last_name',    
        'is_staff', 
        'is_verified'
    )
    list_filter = (
        'is_staff', 
        'is_active', 
        'is_verified'
    )
    
    # Personaliza los fieldsets para mostrar información adicional
    fieldsets = UserAdmin.fieldsets + (
        (None, {
            'fields': (
                'phone_number', 
                'address', 
                'dni', 
                'is_verified'
            )
        }),
    )
    
    # Personaliza los campos para crear nuevos usuarios
    add_fieldsets = UserAdmin.add_fieldsets + (
        (None, {
            'fields': (
                'phone_number', 
                'address', 
                'dni', 
                'is_verified'
            )
        }),
    )

# Registro de modelos de usuario
admin.site.register(User, CustomUserAdmin)

# Personalización opcional del admin de SocialApp
class CustomSocialAppAdmin(BaseSocialAppAdmin):
    def save_model(self, request, obj, form, change):
        # Asegúrate de que solo se guarde la aplicación, sin intentar asociar un usuario
        super().save_model(request, obj, form, change)

# Re-registra SocialApp con la clase personalizada
admin.site.unregister(SocialApp)
admin.site.register(SocialApp, CustomSocialAppAdmin)

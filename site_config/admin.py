from django.contrib import admin
from .models import CarouselImage, SiteImage, SiteSettings

@admin.register(CarouselImage)
class CarouselImageAdmin(admin.ModelAdmin):
    list_display = ('title', 'order', 'active')
    list_editable = ('order', 'active')
    list_filter = ('active',)
    search_fields = ('title', 'subtitle')

@admin.register(SiteImage)
class SiteImageAdmin(admin.ModelAdmin):
    list_display = ('location', 'title')
    search_fields = ('location', 'title')
    fieldsets = (
        (None, {
            'fields': ('location', 'title', 'description', 'image')
        }),
        ('Información adicional para miembros del equipo', {
            'fields': ('bio', 'linkedin_url', 'instagram_url'),
            'classes': ('collapse',),
            'description': 'Estos campos solo son relevantes para las ubicaciones about_team1, about_team2 y about_team3'
        }),
    )

@admin.register(SiteSettings)
class SiteSettingsAdmin(admin.ModelAdmin):
    fieldsets = (
        ('Información Básica', {
            'fields': ('site_name', 'logo', 'favicon', 'footer_text')
        }),
        ('Redes Sociales', {
            'fields': ('facebook_url', 'instagram_url', 'whatsapp_number')
        }),
        ('Información de Contacto', {
            'fields': ('address', 'phone', 'email')
        }),
    )
    
    def has_add_permission(self, request):
        # Solo permitimos una configuración
        return not SiteSettings.objects.exists()
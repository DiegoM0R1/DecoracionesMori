# services/admin.py
from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from .models import ServiceCategory, Service, ServiceImage, ServiceVideo, Product
from .forms import ServiceImageForm, ServiceVideoForm, ServiceForm, ServiceCategoryForm, ProductForm

# Clase base para inlines de imágenes y videos de servicios
class ServiceImageInline(admin.TabularInline):
    model = ServiceImage
    form = ServiceImageForm
    extra = 1
    verbose_name = _("Imagen del servicio")
    verbose_name_plural = _("Imágenes del servicio")
    fields = ('service', 'image', 'image_url', 'is_featured')
    
    def formfield_for_dbfield(self, db_field, **kwargs):
        field = super().formfield_for_dbfield(db_field, **kwargs)
        if db_field.name == 'image':
            field.label = _('Imagen (archivo)')
        elif db_field.name == 'image_url':
            field.label = _('Imagen (URL)')
        elif db_field.name == 'is_featured':
            field.label = _('Destacada')
        return field

class ServiceVideoInline(admin.TabularInline):
    model = ServiceVideo
    form = ServiceVideoForm
    extra = 1
    verbose_name = _("Video del servicio")
    verbose_name_plural = _("Videos del servicio")
    fields = ('service', 'title', 'video', 'video_url')
    
    def formfield_for_dbfield(self, db_field, **kwargs):
        field = super().formfield_for_dbfield(db_field, **kwargs)
        if db_field.name == 'title':
            field.label = _('Título')
        elif db_field.name == 'video':
            field.label = _('Video (archivo)')
        elif db_field.name == 'video_url':
            field.label = _('Video (URL)')
        return field

# Categoría de servicios
@admin.register(ServiceCategory)
class ServiceCategoryAdmin(admin.ModelAdmin):
    form = ServiceCategoryForm
    list_display = ('name', 'description')
    search_fields = ('name',)
    fieldsets = (
        (_('Información de la categoría'), {
            'fields': ('name', 'description')
        }),
    )
    
    def formfield_for_dbfield(self, db_field, **kwargs):
        field = super().formfield_for_dbfield(db_field, **kwargs)
        if db_field.name == 'name':
            field.label = _('Nombre')
        elif db_field.name == 'description':
            field.label = _('Descripción')
        return field

# Servicios (con imágenes y videos integrados como inlines)
@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    form = ServiceForm
    list_display = ('name', 'category', 'base_price', 'is_active', 'created_at')
    list_filter = ('category', 'is_active')
    search_fields = ('name', 'description')
    prepopulated_fields = {'slug': ('name',)}
    inlines = [ServiceImageInline, ServiceVideoInline]
    fieldsets = (
        (_('Información básica'), {
            'fields': ('name', 'slug', 'category', 'description', 'base_price')
        }),
        (_('Estado'), {
            'fields': ('is_active',)
        }),
    )
    
    def formfield_for_dbfield(self, db_field, **kwargs):
        field = super().formfield_for_dbfield(db_field, **kwargs)
        if db_field.name == 'name':
            field.label = _('Nombre')
        elif db_field.name == 'slug':
            field.label = _('Slug')
        elif db_field.name == 'category':
            field.label = _('Categoría')
        elif db_field.name == 'description':
            field.label = _('Descripción')
        elif db_field.name == 'base_price':
            field.label = _('Precio base')
        elif db_field.name == 'is_active':
            field.label = _('Activo')
        elif db_field.name == 'created_at':
            field.label = _('Fecha de creación')
        return field

# Productos
@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    form = ProductForm
    list_display = ('name', 'category', 'price_per_unit', 'unit', 'is_active')
    list_filter = ('category', 'is_active')
    search_fields = ('name', 'description')
    fieldsets = (
        (_('Información del producto'), {
            'fields': ('name', 'category', 'description', 'price_per_unit', 'unit')
        }),
        (_('Estado'), {
            'fields': ('is_active',)
        }),
    )
    
    def formfield_for_dbfield(self, db_field, **kwargs):
        field = super().formfield_for_dbfield(db_field, **kwargs)
        if db_field.name == 'name':
            field.label = _('Nombre')
        elif db_field.name == 'category':
            field.label = _('Categoría')
        elif db_field.name == 'description':
            field.label = _('Descripción')
        elif db_field.name == 'price_per_unit':
            field.label = _('Precio por unidad')
        elif db_field.name == 'unit':
            field.label = _('Unidad')
        elif db_field.name == 'is_active':
            field.label = _('Activo')
        return field

# Personalización de los nombres en la interfaz de administración global
admin.site.site_header = _('Administración del Sitio')
admin.site.site_title = _('Panel de Administración')
admin.site.index_title = _('Bienvenido al Panel de Administración')
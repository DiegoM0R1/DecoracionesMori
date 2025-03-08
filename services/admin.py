from django.contrib import admin

# Register your models here.
from django.contrib import admin
from .models import ServiceCategory, Service, ServiceImage, ServiceVideo, Product

@admin.register(ServiceCategory)
class ServiceCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')
    search_fields = ('name',)

@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'base_price', 'is_active', 'created_at', 'updated_at')
    list_filter = ('category', 'is_active')
    search_fields = ('name', 'description')
    date_hierarchy = 'created_at'

@admin.register(ServiceImage)
class ServiceImageAdmin(admin.ModelAdmin):
    list_display = ('service', 'image', 'is_featured')
    list_filter = ('is_featured',)
    search_fields = ('service__name',)

@admin.register(ServiceVideo)
class ServiceVideoAdmin(admin.ModelAdmin):
    list_display = ('service', 'title', 'video')
    search_fields = ('service__name', 'title')

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'price_per_unit', 'unit', 'is_active')
    list_filter = ('category', 'is_active')
    search_fields = ('name', 'description')
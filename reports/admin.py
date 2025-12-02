from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html
from django.shortcuts import redirect
from .models import ReporteDummy

@admin.register(ReporteDummy)
class ReporteDummyAdmin(admin.ModelAdmin):
    """
    Admin del modelo dummy que redirige al reporte de ventas.
    """
    
    def has_add_permission(self, request):
        """Ocultar botón 'Agregar'"""
        return False
    
    def has_delete_permission(self, request, obj=None):
        """Ocultar botón 'Eliminar'"""
        return False
    
    def has_change_permission(self, request, obj=None):
        """Ocultar botón 'Modificar'"""
        return False
    
    def changelist_view(self, request, extra_context=None):
        """
        Cuando el usuario haga clic en 'Reportes' en el menú,
        lo redirigimos directamente al reporte de ventas.
        """
        return redirect('reports:sales_report')
    
    # Esto hace que no se muestre ningún objeto en la lista
    def get_queryset(self, request):
        return ReporteDummy.objects.none()
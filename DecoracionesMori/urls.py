"""
URL configuration for DecoracionesMori project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
"""
URL configuration for DecoracionesMori project.
"""
from django.contrib import admin
from django.urls import path, include
from django.views.generic import TemplateView
from django.conf import settings
from django.conf.urls.static import static
from services.views import HomeView
from django.utils.translation import gettext_lazy as _

# Importaciones para el dashboard
from django.http import JsonResponse
from django.db.models import Count
from django.db.models.functions import TruncMonth, TruncDate
from django.contrib.admin.views.decorators import staff_member_required
from appointments.models import Appointment
from services.models import Service
from clients.models import ClientProfile
from django.views.generic import RedirectView

# Vista para el dashboard directamente en urls.py
@staff_member_required
def dashboard_data(request):
    """Proporciona datos JSON para el dashboard"""
    try:
        # 1. Citas por estado
        appointments_by_status = list(
            Appointment.objects.values('status')
            .annotate(count=Count('id'))
            .order_by('status')
        )
        
        # 2. Servicios más solicitados
        top_services = list(
            Appointment.objects.values('service__name')
            .annotate(count=Count('id'))
            .order_by('-count')[:5]
        )
        
        # 3. Citas por mes
        appointments_by_month = list(
            Appointment.objects.annotate(month=TruncMonth('appointment_date'))
            .values('month')
            .annotate(count=Count('id'))
            .order_by('month')
        )
        
        # 4. Clientes por tipo
        clients_by_type = list(
            ClientProfile.objects.values('client_type')
            .annotate(count=Count('id'))
            .order_by('client_type')
        )
        
        # 5. Citas recientes (últimos 30 días)
        recent_appointments = list(
            Appointment.objects.annotate(date=TruncDate('appointment_date'))
            .values('date')
            .annotate(count=Count('id'))
            .order_by('-date')[:30]
        )
        
        data = {
            'appointments_by_status': appointments_by_status,
            'top_services': top_services,
            'appointments_by_month': appointments_by_month,
            'clients_by_type': clients_by_type,
            'recent_appointments': recent_appointments
        }
        
        return JsonResponse(data)
    except Exception as e:
        import traceback
        print(f"Error en dashboard_data: {str(e)}")
        print(traceback.format_exc())
        return JsonResponse({'error': str(e)}, status=500)

# IMPORTANTE: Definimos primero la ruta específica del dashboard antes de la ruta general de admin
urlpatterns = [
    path('admin/dashboard-data/', dashboard_data, name='dashboard-data'),
    path('admin/', admin.site.urls),
    
    path('', HomeView.as_view(template_name='home.html'), name='home'),
    path('home/', HomeView.as_view(template_name='home.html'), name='home'),
    path('nosotros/', TemplateView.as_view(template_name='nosotros.html'), name='nosotros'),
    path('contacto/', TemplateView.as_view(template_name='contacto.html'), name='contacto'),
    
    path('servicios/', include('services.urls', namespace='services')),
    path('appointments/', include('appointments.urls', namespace='appointments')),
    path('accounts/', include('accounts.urls', namespace='accounts')),
    path('accounts/', include('allauth.urls')),
    path('invoices/', include('invoices.urls', namespace='invoices')),
    path('inventory/', include('inventory.urls')),
    
    # Redirección para accesos directos a secciones de inventario desde el panel lateral
    path('admin/inventory/inventorystatus/', 
         RedirectView.as_view(url='/admin/inventory/inventorystatus/', permanent=False)),
    path('admin/inventory/inventorymovement/',
         RedirectView.as_view(url='/admin/inventory/inventorymovement/', permanent=False)),

    path('admin/inventory/inventory_report/',
         RedirectView.as_view(url='/admin/inventory/inventory_report/', permanent=False)),

    
]
    


# Servir archivos estáticos en desarrollo
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
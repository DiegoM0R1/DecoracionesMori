from django.contrib import admin
from django.http import JsonResponse
from django.urls import path
from django.db.models import Count
from django.db.models.functions import TruncMonth, TruncDate
from django.utils.translation import gettext_lazy as _
from django.contrib.admin.sites import AdminSite

# Importar los modelos relevantes
from appointments.models import Appointment
from services.models import Service
from clients.models import ClientProfile

# Vista para los datos del dashboard
def get_dashboard_data(request):
    """Proporciona datos JSON para el dashboard"""
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

# Agregar la URL personalizada al AdminSite
original_get_urls = AdminSite.get_urls

def custom_get_urls(self):
    urls = original_get_urls(self)
    custom_urls = [
        path('dashboard-data/', self.admin_view(get_dashboard_data), name='dashboard-data'),
    ]
    return custom_urls + urls

# Aplicar el método personalizado
AdminSite.get_urls = custom_get_urls


from django.contrib import admin
from django.utils.translation import gettext_lazy as _

# Personalización del sitio admin
admin.site.site_header = _('Administración DecoracionesMori')
admin.site.site_title = _('Panel de Control')
admin.site.index_title = _('Dashboard DecoracionesMori')

# No es necesario modificar el método get_urls de AdminSite
# Las URLs ya se manejan en dashboard.py que se debe incluir en urls.py
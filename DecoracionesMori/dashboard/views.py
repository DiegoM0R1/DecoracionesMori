from django.http import JsonResponse
from django.db.models import Count
from django.db.models.functions import TruncMonth, TruncDate
from django.contrib.admin.views.decorators import staff_member_required

# Importar los modelos relevantes
from appointments.models import Appointment
from services.models import Service
from clients.models import ClientProfile

@staff_member_required
def dashboard_data(request):
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
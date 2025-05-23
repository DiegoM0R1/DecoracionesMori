from django.http import JsonResponse
from django.db.models import Count
from django.db.models.functions import TruncMonth, TruncDate
from django.contrib.admin.views.decorators import staff_member_required
from django.utils.translation import gettext_lazy as _
from django.urls import path

# Importar los modelos relevantes
from appointments.models import Appointment
from services.models import Service
from clients.models import ClientProfile

@staff_member_required
def dashboard_data(request):
    """Proporciona datos JSON para el dashboard"""
    try:
        # === CITAS ===
        # 1. Citas por estado
        appointments_by_status = list(
            Appointment.objects.values('status')
            .annotate(count=Count('id'))
            .order_by('status')
        )
        
        # 2. Citas por mes (últimos 12 meses)
        from datetime import datetime, timedelta
        end_date = datetime.now()
        start_date = end_date - timedelta(days=365)
        
        appointments_by_month = list(
            Appointment.objects.filter(
                appointment_date__gte=start_date,
                appointment_date__lte=end_date
            )
            .annotate(month=TruncMonth('appointment_date'))
            .values('month')
            .annotate(count=Count('id'))
            .order_by('month')
        )
        
        # 3. Citas recientes (últimos 30 días)
        recent_appointments = list(
            Appointment.objects.filter(
                appointment_date__gte=end_date - timedelta(days=30)
            )
            .annotate(date=TruncDate('appointment_date'))
            .values('date')
            .annotate(count=Count('id'))
            .order_by('date')
        )
        
        # 4. Duración promedio de citas
        from django.db.models import Avg, F, ExpressionWrapper, fields
        try:
            # Intentar calcular la duración promedio
            avg_duration = Appointment.objects.filter(
                end_time__isnull=False
            ).aggregate(
                avg_duration=Avg(
                    ExpressionWrapper(
                        F('end_time') - F('start_time'), 
                        output_field=fields.DurationField()
                    )
                )
            )
            avg_duration_minutes = avg_duration['avg_duration'].total_seconds() / 60 if avg_duration['avg_duration'] else 0
        except:
            # Si hay error, es probable que los campos no existan
            avg_duration_minutes = 0
        
        # === SERVICIOS ===
        # 5. Servicios más solicitados
        top_services = list(
            Appointment.objects.values('service__name')
            .annotate(count=Count('id'))
            .order_by('-count')[:8]
        )
        
        # 6. Ingresos por servicio
        try:
            # Intenta obtener ingresos por servicio (si existe un campo price/cost)
            revenue_by_service = list(
                Appointment.objects.filter(status='COMPLETED')
                .values('service__name')
                .annotate(total=Sum('service__price'))
                .order_by('-total')[:8]
            )
        except:
            # Fallback si no hay campo de precio
            revenue_by_service = []
        
        # === CLIENTES ===
        # 7. Clientes por tipo
        clients_by_type = list(
            ClientProfile.objects.values('client_type')
            .annotate(count=Count('id'))
            .order_by('client_type')
        )
        
        # 8. Nuevos clientes por mes
        try:
            new_clients_by_month = list(
                ClientProfile.objects.filter(
                    date_joined__gte=start_date,
                    date_joined__lte=end_date
                )
                .annotate(month=TruncMonth('date_joined'))
                .values('month')
                .annotate(count=Count('id'))
                .order_by('month')
            )
        except:
            # Si no hay campo date_joined
            new_clients_by_month = []
        
        # === FACTURACIÓN ===
        # 9. Ingresos por mes
        try:
            from invoices.models import Invoice
            revenue_by_month = list(
                Invoice.objects.filter(
                    date__gte=start_date,
                    date__lte=end_date,
                    status='PAID'
                )
                .annotate(month=TruncMonth('date'))
                .values('month')
                .annotate(total=Sum('total_amount'))
                .order_by('month')
            )
        except:
            # Si no existe el modelo o campos
            revenue_by_month = []
        
        # === PRODUCTOS ===
        # 10. Productos más vendidos
        try:
            from inventory.models import Product
            top_products = list(
                Product.objects.values('name')
                .annotate(count=Count('orderitem'))
                .order_by('-count')[:8]
            )
        except:
            # Si no existe el modelo
            top_products = []
        
        # Prepara todos los datos
        data = {
            # Citas
            'appointments_by_status': appointments_by_status,
            'appointments_by_month': appointments_by_month,
            'recent_appointments': recent_appointments,
            'avg_appointment_duration': avg_duration_minutes,
            
            # Servicios
            'top_services': top_services,
            'revenue_by_service': revenue_by_service,
            
            # Clientes
            'clients_by_type': clients_by_type,
            'new_clients_by_month': new_clients_by_month,
            
            # Facturación
            'revenue_by_month': revenue_by_month,
            
            # Productos
            'top_products': top_products
        }
        
        return JsonResponse(data)
    except Exception as e:
        import traceback
        print(f"Error en dashboard_data: {str(e)}")
        print(traceback.format_exc())
        return JsonResponse({'error': str(e)}, status=500)
# appointments/urls.py
from django.urls import path
from django.views.generic import TemplateView
from .views import (
    appointment_list,
    AppointmentRequestView, # Mantenemos la CBV
    # AppointmentCalendarView, # Comentado hasta que se redefina
    buscar_cliente_por_dni,
    appointment_detail,
    get_availabilities,
    get_daily_availability_status,
)
from .views import cancel_appointment_view # Importa la vista de cancelación
from django.utils.translation import gettext_lazy as _

app_name = 'appointments'

urlpatterns = [
    # --- Vistas Principales y de Lista ---
    path('', appointment_list, name='appointment_list'),
    # path('calendar/', AppointmentCalendarView.as_view(), name='calendar'), # Ruta comentada

    # --- Proceso de Solicitud y Éxito ---
    path('request/<int:service_id>/', AppointmentRequestView.as_view(), name='request'), # Ruta principal para solicitar
    path('success/', TemplateView.as_view(template_name='appointments/success.html'), name='success'), # Página de éxito genérica

    # --- Detalles y Acciones Específicas ---
    path('<int:appointment_id>/', appointment_detail, name='appointment_detail'),
    path('api/daily-availability/', get_daily_availability_status, name='api_daily_availability'),
    # --- Endpoints Auxiliares / API ---
    path('buscar-dni/', buscar_cliente_por_dni, name='buscar_dni'),
    path('api/disponibilidades/', get_availabilities, name='get_availabilities'), # API actualizada (básica)
    path('cancel/<int:appointment_id>/', cancel_appointment_view, name='cancel_appointment'),

    # --- Otras (si aplican) ---
    # path('home/', TemplateView.as_view(template_name='home.html'), name='home'), # Evalúa si es necesaria
]
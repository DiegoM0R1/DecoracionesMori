from django.urls import path
from .views import AppointmentRequestView, AppointmentCalendarView, buscar_cliente_por_dni
from django.views.generic import TemplateView
from . import views

app_name = 'appointments'

urlpatterns = [
    path('', views.appointment_list, name='appointment_list'),
    # Elimina esta línea ya que client_dashboard se mueve a accounts
    # path('dashboard/', views.client_dashboard, name='client_dashboard'),
    
    path('home/', TemplateView.as_view(template_name='home.html'), name='home'),
    
    # Usa solo una de estas dos rutas para solicitar citas (o la vista basada en clase o la función)
    path('request/<int:service_id>/', views.AppointmentRequestView.as_view(), name='request'),
    path('solicitar/', views.request_appointment, name='request_appointment'),
    
    path('calendar/', views.AppointmentCalendarView.as_view(), name='calendar'),
    path('buscar-dni/', views.buscar_cliente_por_dni, name='buscar_dni'),
    path('success/', TemplateView.as_view(template_name='appointments/success.html'), name='success'),
    path('<int:appointment_id>/', views.appointment_detail, name='appointment_detail'),
    path('api/disponibilidades/', views.get_availabilities, name='get_availabilities'),
]


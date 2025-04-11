from django.urls import path
from .views import AppointmentRequestView, AppointmentCalendarView, buscar_cliente_por_dni
from django.views.generic import TemplateView
from . import views

app_name = 'appointments'

urlpatterns = [
    path('', views.appointment_list, name='appointment_list'),
    path('home/', TemplateView.as_view(template_name='home.html'), name='home'),
    path('request/<int:service_id>/', AppointmentRequestView.as_view(), name='request'),
    path('calendar/', AppointmentCalendarView.as_view(), name='calendar'),
    path('buscar-dni/', buscar_cliente_por_dni, name='buscar_dni'),
    path('success/', TemplateView.as_view(template_name='appointments/success.html'), name='success'),
    path('<int:appointment_id>/', views.appointment_detail, name='appointment_detail'),
    path('solicitar/', views.request_appointment, name='request_appointment'),
    path('api/disponibilidades/', views.get_availabilities, name='get_availabilities'),
    
]


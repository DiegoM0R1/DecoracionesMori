from django.urls import path
from .views import AppointmentRequestView, AppointmentCalendarView, buscar_cliente_por_dni
from django.views.generic import TemplateView

app_name = 'appointments'

urlpatterns = [
    path('', TemplateView.as_view(template_name='home.html'), name='home'),
    path('home/', TemplateView.as_view(template_name='home.html'), name='home'),
    path('request/<int:service_id>/', AppointmentRequestView.as_view(), name='request'),
    path('calendar/', AppointmentCalendarView.as_view(), name='calendar'),
    path('buscar-dni/', buscar_cliente_por_dni, name='buscar_dni'),

]
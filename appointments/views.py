# appointments/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import CreateView, DetailView, ListView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.http import JsonResponse
from .models import Appointment, StaffAvailability
from .forms import AppointmentRequestForm
from accounts.models import User
from services.models import Service
from django.utils import timezone

class AppointmentCalendarView(LoginRequiredMixin, ListView):
    template_name = 'appointments/calendar.html'
    model = StaffAvailability
    context_object_name = 'availabilities'
    
    def get_queryset(self):
        queryset = super().get_queryset()
        # Only show future availabilities
        return queryset.filter(date__gte=timezone.now().date(), is_available=True)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['service_id'] = self.request.GET.get('service')
        return context

class AppointmentRequestView(CreateView):
    model = Appointment
    form_class = AppointmentRequestForm
    template_name = 'appointments/request_appointment.html'
    success_url = reverse_lazy('appointment_success')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        service_id = self.kwargs.get('service_id')
        service = get_object_or_404(Service, pk=service_id)
        kwargs['initial'] = {'service': service}
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        service_id = self.kwargs.get('service_id')
        context['service'] = get_object_or_404(Service, pk=service_id)
        return context

    def form_valid(self, form):
        # Obtener el servicio seleccionado
        service_id = self.kwargs.get('service_id')
        service = get_object_or_404(Service, pk=service_id)

        # Check if user exists, if not create one
        email = form.cleaned_data['email']
        user, created = User.objects.get_or_create(
            email=email,
            defaults={
                'username': email,
                'dni': form.cleaned_data['dni'],
                'phone_number': form.cleaned_data['phone_number'],
                'address': form.cleaned_data['address'],
                'first_name': form.cleaned_data['name'].split(' ')[0],
                'last_name': ' '.join(form.cleaned_data['name'].split(' ')[1:]),
            }
        )

        # Create appointment
        appointment = form.save(commit=False)
        appointment.client = user
        appointment.service = service  # Asignar el servicio explícitamente

        # Find staff availability
        preferred_date = form.cleaned_data['preferred_date']
        preferred_time = form.cleaned_data['preferred_time']

        # Logic to find an available staff member
        availabilities = StaffAvailability.objects.filter(
            date=preferred_date,
            is_available=True
        )

        if availabilities.exists():
            appointment.staff_availability = availabilities.first()

from django.views.decorators.csrf import csrf_exempt

import requests

@csrf_exempt
def buscar_cliente_por_dni(request):
    if request.method == 'POST':
        dni = request.POST.get('dni')
        if not dni:
            return JsonResponse({'error': 'DNI es requerido'}, status=400)
        
        token = 'de3e5dc9486d29e79d5d497fa4082ba9f18472e6a1ec9686de1e35e6c0be81d7'
        
        try:
            url = f'https://apiperu.dev/api/dni/{dni}?api_token={token}'
            response = requests.get(url)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    return JsonResponse({
                        'nombre': data['data'].get('nombre_completo', ''),
                        'dni': dni,
                    })
            
            return JsonResponse({
                'error': 'No se encontraron datos para el DNI proporcionado'
            }, status=404)
            
        except Exception as e:
            return JsonResponse({'error': f'Error de conexión: {str(e)}'}, status=500)
    
    return JsonResponse({'error': 'Método no permitido'}, status=405)
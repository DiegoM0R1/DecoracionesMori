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
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from django.views.generic import TemplateView

class AppointmentCalendarView(LoginRequiredMixin, TemplateView):
    template_name = 'appointments/calendar.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.user.is_staff:
            # Staff see all appointments
            context['appointments'] = Appointment.objects.all().select_related('client', 'service', 'staff_availability')
        else:
            # Clients see only their appointments
            context['appointments'] = Appointment.objects.filter(client=self.request.user).select_related('service', 'staff_availability')
        return context

class AppointmentRequestView(CreateView):
    model = Appointment
    form_class = AppointmentRequestForm
    template_name = 'appointments/request_form.html'
    success_url = reverse_lazy('appointments:success')

    def get_initial(self):
        initial = super().get_initial()
        service_id = self.kwargs.get('service_id')
        if service_id:
            initial['service'] = get_object_or_404(Service, pk=service_id)
        return initial

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        service_id = self.kwargs.get('service_id')
        context['service'] = get_object_or_404(Service, pk=service_id)
        return context

    def form_valid(self, form):
        # Get form data
        dni = form.cleaned_data.get('dni')
        name = form.cleaned_data.get('name')
        email = form.cleaned_data.get('email')
        phone_number = form.cleaned_data.get('phone_number')
        address = form.cleaned_data.get('address')
        
        # Parse name into first_name and last_name
        name_parts = name.split()
        first_name = name_parts[0] if name_parts else ""
        last_name = " ".join(name_parts[1:]) if len(name_parts) > 1 else ""
        
        print(f"Processing appointment for DNI: {dni}, Name: {name}")  # Debug print
        
        # Try to find existing user by DNI
        try:
            client = User.objects.get(dni=dni)
            # Update user data if needed
            if client.first_name != first_name:
                client.first_name = first_name
            if client.last_name != last_name:
                client.last_name = last_name
            if client.email != email:
                client.email = email
            if client.phone_number != phone_number:
                client.phone_number = phone_number
            if client.address != address:
                client.address = address
            client.save()
            print(f"Updated existing user: {client.username}")  # Debug print
        except User.DoesNotExist:
            # Create new user with provided data
            username = email.split('@')[0]
            # Check if username exists and make it unique if needed
            counter = 1
            original_username = username
            while User.objects.filter(username=username).exists():
                username = f"{original_username}{counter}"
                counter += 1
                
            print(f"Creating new user with username: {username}")  # Debug print
            
            # Create user with basic data
            client = User.objects.create_user(
                username=username,
                email=email,
                password=User.objects.make_random_password(),  # Generate a random password
                first_name=first_name,
                last_name=last_name,
                dni=dni,
                phone_number=phone_number,
                address=address,
                is_active=True
            )
        
        # Create appointment
        appointment = form.save(commit=False)
        appointment.client = client
        appointment.service = form.cleaned_data.get('service')
        
        # Find available staff based on preferred date and time
        preferred_date = form.cleaned_data.get('preferred_date')
        preferred_time = form.cleaned_data.get('preferred_time')
        
        # Find a suitable staff availability slot
        staff_availability = None
        if preferred_time == 'morning':
            staff_availability = StaffAvailability.objects.filter(
                date=preferred_date,
                start_time__hour__lt=12,
                is_available=True
            ).first()
        elif preferred_time == 'afternoon':
            staff_availability = StaffAvailability.objects.filter(
                date=preferred_date,
                start_time__hour__gte=13,
                is_available=True
            ).first()
            
        if staff_availability:
            appointment.staff_availability = staff_availability
            # Mark the slot as unavailable
            staff_availability.is_available = False
            staff_availability.save()
            print(f"Assigned staff availability: {staff_availability}")  # Debug print
        else:
            print(f"No staff availability found for date: {preferred_date}, time: {preferred_time}")  # Debug print
        
        appointment.save()
        print(f"Appointment saved with ID: {appointment.id}")  # Debug print
        
        messages.success(self.request, _("Su solicitud de cita ha sido registrada. Nos pondremos en contacto con usted pronto."))
        return redirect(self.success_url)

    def form_invalid(self, form):
        print(f"Form is invalid: {form.errors}")  # Debug print
        messages.error(self.request, _("Por favor corrija los errores en el formulario."))
        return super().form_invalid(form)


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

class AppointmentSuccessView(TemplateView):
    template_name = 'appointments/success.html'
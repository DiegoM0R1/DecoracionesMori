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
    
    def form_valid(self, form):
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
        
        # Find staff availability
        preferred_date = form.cleaned_data['preferred_date']
        preferred_time = form.cleaned_data['preferred_time']
        
        # Logic to find an available staff member
        # In a real implementation, you'd have more sophisticated logic
        availabilities = StaffAvailability.objects.filter(
            date=preferred_date,
            is_available=True
        )
        
        if availabilities.exists():
            appointment.staff_availability = availabilities.first()
        
        appointment.save()
        return super().form_valid(form)
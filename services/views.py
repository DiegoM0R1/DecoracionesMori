# services/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView, DetailView, CreateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from .models import Service, ServiceCategory
from appointments.forms import AppointmentRequestForm

class ServiceListView(ListView):
    model = Service
    context_object_name = 'services'
    template_name = 'services/service_list.html'
    
    def get_queryset(self):
        queryset = super().get_queryset().filter(is_active=True)
        category = self.request.GET.get('category')
        if category:
            queryset = queryset.filter(category__id=category)
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = ServiceCategory.objects.all()
        return context

class ServiceDetailView(DetailView):
    model = Service
    context_object_name = 'service'
    template_name = 'services/service_detail.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['request_form'] = AppointmentRequestForm(initial={'service': self.object})
        return context


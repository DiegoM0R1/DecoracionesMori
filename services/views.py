from django.shortcuts import render, get_object_or_404
from django.views.generic import ListView, DetailView
from .models import Service, ServiceCategory

class ServiceListView(ListView):
    model = Service
    context_object_name = 'services'
    template_name = 'services/service_list.html'
    
    def get_queryset(self):
        queryset = super().get_queryset().filter(is_active=True)
        category_id = self.kwargs.get('id')
        if category_id:
            queryset = queryset.filter(category__id=category_id)
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = ServiceCategory.objects.all()
        context['categoria_actual'] = None
        category_id = self.kwargs.get('id')
        if category_id:
            context['categoria_actual'] = get_object_or_404(ServiceCategory, id=category_id)
        return context

class ServiceDetailView(DetailView):
    model = Service
    context_object_name = 'service'
    template_name = 'services/service_detail.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['imagenes'] = self.object.images.all()
        context['videos'] = self.object.videos.all()
        context['servicios_relacionados'] = Service.objects.filter(category=self.object.category).exclude(id=self.object.id)[:5]
        return context
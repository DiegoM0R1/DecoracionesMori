from django.shortcuts import render, get_object_or_404
from django.views.generic import ListView, DetailView
from .models import Service, ServiceCategory
from django.views.generic import TemplateView

class HomeView(TemplateView):
    template_name = 'home.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Obtener todas las categorías y un servicio de cada una
        categories = ServiceCategory.objects.all()
        categories_with_service = []
        for category in categories:
            service = Service.objects.filter(category=category, is_active=True).first()
            if service:
                categories_with_service.append({
                    'category': category,
                    'service': service
                })
        context['categories_with_service'] = categories_with_service
        return context
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
        # Añadir contexto para el modal de login si no está autenticado
        if not self.request.user.is_authenticated:
            context['show_login_modal'] = True
        return context
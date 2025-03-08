from django.urls import path
from .views import ServiceListView, ServiceDetailView
from django.views.generic import TemplateView

app_name = 'services'

urlpatterns = [
    
    path('', TemplateView.as_view(template_name='home.html'), name='home'),
    path('home/', TemplateView.as_view(template_name='home.html'), name='home'),
    path('servicios/', ServiceListView.as_view(), name='service_list'),
    path('<int:pk>/', ServiceDetailView.as_view(), name='detalle_servicio'),
    path('categoria/<int:id>/', ServiceListView.as_view(), name='category'),
]
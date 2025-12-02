from django.urls import path
from .views import ServiceListView, ServiceDetailView, get_product_data, get_service_data, vista_cotizacion, generar_pdf_cotizacion, contacto_view
from django.http import JsonResponse
from django.views.generic import TemplateView

app_name = 'services'

urlpatterns = [
    
    path('', TemplateView.as_view(template_name='home.html'), name='home'),
    path('home/', TemplateView.as_view(template_name='home.html'), name='home'),
    path('nosotros/', TemplateView.as_view(template_name='nosotros.html'), name='nosotros'),

    path('servicios/', ServiceListView.as_view(), name='service_list'),
    path('<int:pk>/', ServiceDetailView.as_view(), name='detalle_servicio'),
    path('categoria/<int:id>/', ServiceListView.as_view(), name='category'),
    path('cotizar/<int:service_id>/', vista_cotizacion, name='cotizar'),
    path('generar-pdf-cotizacion/<int:service_id>/', generar_pdf_cotizacion, name='generar_pdf_cotizacion'),
    path('contacto/', contacto_view, name='contacto'),

    # API endpoints
    path('admin/api/products/<int:product_id>/', get_product_data, name='get_product_data'),
    path('admin/api/services/<int:service_id>/', get_service_data, name='get_service_data'),
]
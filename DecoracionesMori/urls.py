"""
URL configuration for DecoracionesMori project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.views.generic import TemplateView
from django.conf import settings
from django.conf.urls.static import static

# Personalización del panel de administración
admin.site.site_header = "Panel de Administración de Decoraciones Mori"
admin.site.site_title = "Panel Administrativo"
admin.site.index_title = "Bienvenido al Panel de Administración"

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', TemplateView.as_view(template_name='home.html'), name='home'),
    path('home/', TemplateView.as_view(template_name='home.html'), name='home'),
    path('nosotros/', TemplateView.as_view(template_name='nosotros.html'), name='nosotros'),
    path('contacto/', TemplateView.as_view(template_name='contacto.html'), name='contacto'),

    path('servicios/', include('services.urls', namespace='services')),
    path('appointments/', include('appointments.urls', namespace='appointments')),
    path('accounts/', include('accounts.urls', namespace='accounts')),
    path('accounts/', include('allauth.urls')),  # URLs de allauth para autenticación
    path('cotizaciones/', include('quotations.urls', namespace='quotations')),


]
# Servir archivos estáticos en desarrollo
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

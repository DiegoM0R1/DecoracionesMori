from django.urls import path
from .views import ServiceListView, ServiceDetailView

app_name = 'services'

urlpatterns = [
    path('', ServiceListView.as_view(), name='lista_servicios'),
    path('<int:pk>/', ServiceDetailView.as_view(), name='detalle_servicio'),
]
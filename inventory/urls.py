# inventory/urls.py
from django.urls import path
from .views import inventory_report, product_history

app_name = 'inventory'

urlpatterns = [
    # Estas URLs son para acceso directo, pero preferimos usar las rutas del admin
    path('reporte/', inventory_report, name='inventory_report_direct'),
    path('producto/<int:product_id>/historial/', product_history, name='product_history_direct'),
]
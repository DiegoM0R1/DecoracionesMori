# invoices/urls.py
from django.urls import path
from . import views

app_name = 'invoices'


urlpatterns = [
    path('admin/invoice/<int:invoice_id>/print/', views.print_invoice, name='print_invoice'),
    path('print/<int:invoice_id>/', views.client_print_invoice, name='client_print_invoice'),
    path('admin/invoice/<int:invoice_id>/register-payment/', views.register_pending_payment, name='register_pending_payment'),

]
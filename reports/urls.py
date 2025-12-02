from django.urls import path
from . import views

app_name = 'reports'

urlpatterns = [
    path('', views.sales_report_view, name='sales_report'),
    path('download/csv/', views.download_csv_view, name='download_csv'),
    path('download/pdf/', views.download_pdf_view, name='download_pdf'),
]

from django.urls import path
from .views import client_login, client_logout, client_dashboard, client_profile
from django.views.generic import TemplateView
app_name = 'accounts'  # Add this line

urlpatterns = [
    # URLs para clientes
    path('', TemplateView.as_view(template_name='home.html'), name='home'),
    path('home/', TemplateView.as_view(template_name='home.html'), name='home'),
    path('login/', client_login, name='login'),
    path('logout/', client_logout, name='logout'),
    path('dashboard/', client_dashboard, name='dashboard'),  # Ensure this line is present
    path('profile/', client_profile, name='profile'),  # Ensure this line is present
]
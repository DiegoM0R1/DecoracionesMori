
from django.urls import path
from . import views

urlpatterns = [
    # URLs para clientes
    path('', views.client_login, name='client_login'),
    path('logout/', views.client_logout, name='client_logout'),
    path('dashboard/', views.client_dashboard, name='client_dashboard'),
    path('perfil/', views.client_profile, name='client_profile'),
]
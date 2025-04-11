from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .models import User
from allauth.account.views import SignupView, LoginView
from django.urls import reverse_lazy



def client_login(request):
    """Vista para el login de clientes"""
    if request.user.is_authenticated:
        if request.user.is_staff:
            return redirect('admin:index')  # Personal administrativo va al admin
        else:
            return redirect('/') 

def client_logout(request):
    """Vista para cerrar sesión de clientes"""
    logout(request)
    return redirect('client_login')

# En accounts/views.py (asegúrate de que esta función esté correctamente implementada)
@login_required(login_url='account_login')  # Cambiado a account_login para usar allauth
def client_dashboard(request):
    """Dashboard para clientes, donde pueden ver sus citas y cotizaciones"""
    # Solo mostrar si el usuario es un cliente (no staff)
    if request.user.is_staff:
        return redirect('admin:index')
    
    # Obtenemos las citas del cliente
    appointments = request.user.appointments.all().order_by('-created_at')
    
    # Obtenemos las cotizaciones del cliente
    quotations = request.user.quotations.all().order_by('-created_at')
    
    context = {
        'appointments': appointments,
        'quotations': quotations,
    }
    
    return render(request, 'accounts/client_dashboard.html', context)

@login_required(login_url='client_login')
def client_profile(request):
    """Vista para que el cliente vea y edite su perfil"""
    if request.method == 'POST':
        # Obtener datos del formulario
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        email = request.POST.get('email')
        phone_number = request.POST.get('phone_number')
        address = request.POST.get('address')
        
        # Actualizar usuario
        user = request.user
        user.first_name = first_name
        user.last_name = last_name
        user.email = email
        user.phone_number = phone_number
        user.address = address
        user.save()
        
        messages.success(request, 'Perfil actualizado correctamente.')
        return redirect('client_profile')
    
    return render(request, 'accounts/client_profile.html')
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from .forms import UserLoginForm
from django.contrib.auth.decorators import login_required
from .forms import UserRegistrationForm, UserUpdateForm

def user_login_view(request):
    """
    Vista para el inicio de sesión de usuarios
    """
    if request.method == 'POST':
        form = UserLoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = authenticate(request, username=username, password=password)
            
            if user is not None:
                login(request, user)
                messages.success(request, "Has iniciado sesión correctamente.")
                return redirect('home')  # O la URL que prefieras después del login
            else:
                messages.error(request, "Nombre de usuario o contraseña incorrectos.")
    else:
        form = UserLoginForm()
    
    return render(request, 'accounts/login.html', {'form': form})

def user_logout_view(request):
    """
    Vista para cerrar sesión de usuarios
    """
    logout(request)
    messages.success(request, "Has cerrado sesión correctamente.")
    return redirect('home')  # O la URL que prefieras después del logout

def register_view(request):
    """
    Vista para el registro de nuevos usuarios
    """
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            # Iniciar sesión automáticamente después del registro
            username = form.cleaned_data.get('username')
            raw_password = form.cleaned_data.get('password1')
            user = authenticate(username=username, password=raw_password)
            
            if user is not None:
                login(request, user)
                messages.success(request, f"Registro exitoso. Bienvenido {username}!")
                return redirect('home')  # Cambia 'home' por la URL deseada después del registro
    else:
        form = UserRegistrationForm()
    
    return render(request, 'accounts/register.html', {'form': form})

@login_required
def profile_view(request):
    """
    Vista para el perfil de usuario
    """
    if request.method == 'POST':
        form = UserUpdateForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Tu perfil ha sido actualizado exitosamente.")
            return redirect('profile')
    else:
        form = UserUpdateForm(instance=request.user)
    
    return render(request, 'accounts/profile.html', {'form': form})
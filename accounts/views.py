from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from .forms import UserLoginForm
from django.contrib.auth.decorators import login_required
from .forms import UserRegistrationForm, UserUpdateForm

# accounts/views.py
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
                if user.is_verified:
                    login(request, user)
                    messages.success(request, "Has iniciado sesión correctamente.")
                    return redirect('home')  # O la URL que prefieras después del login
                else:
                    messages.error(request, "Tu cuenta no está verificada. Por favor, verifica tu correo electrónico.")
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

# En accounts/views.py
def register_view(request):
    """
    Vista para el registro de nuevos usuarios
    """
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            # Guarda el usuario (desactivado)
            user = form.save()
            # Genera y envía el correo de verificación
            form.send_verification_email(user, request)
            
            messages.success(request, f"Registro exitoso. Se ha enviado un correo de verificación a tu dirección de email.")
            return redirect('accounts:verification_sent')
    else:
        form = UserRegistrationForm()
    
    return render(request, 'accounts/register.html', {'form': form})

def send_verification_email(request, user):
    """
    Enviar correo de verificación
    """
    # Generar token único
    from django.utils.crypto import get_random_string
    from django.urls import reverse
    from django.conf import settings
    import uuid
    
    token = uuid.uuid4().hex
    
    # Guardar token
    from django.core.cache import cache
    cache_key = f"email_verification_{user.email}"
    cache.set(cache_key, token, timeout=86400)  # 24 horas
    
    # Crear URL de verificación con namespace
    site_url = settings.SITE_URL or request.build_absolute_uri('/').rstrip('/')
    verification_url = f"{site_url}{reverse('accounts:verify_email', kwargs={'email': user.email, 'token': token})}"
    
    # Enviar email
    from django.core.mail import send_mail
    subject = "Verifica tu correo electrónico"
    message = f"""
    Hola {user.username},
    
    Gracias por registrarte. Por favor, verifica tu correo electrónico haciendo clic en el siguiente enlace:
    
    {verification_url}
    
    Este enlace expirará en 24 horas.
    
    Saludos,
    El equipo de Decoraciones Mori
    """
    
    send_mail(
        subject=subject,
        message=message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
        fail_silently=False
    )
    
    print(f"Correo de verificación enviado a {user.email} con token {token}")

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

def verification_sent(request):
    """
    Vista para mostrar mensaje después del registro
    """
    return render(request, 'accounts/verification_sent.html')

# accounts/views.py
def verify_email(request, email, token):
    """
    Vista para verificar correo electrónico
    """
    from django.core.cache import cache
    from django.contrib.auth import get_user_model
    
    User = get_user_model()
    cache_key = f"email_verification_{email}"
    stored_token = cache.get(cache_key)
    
    if stored_token and stored_token == token:
        try:
            # Obtener el usuario con este email
            user = User.objects.get(email=email)
            user.is_verified = True  # Marcar como verificado
            user.save()
            
            # Limpia el token de verificación
            cache.delete(cache_key)
            
            messages.success(request, "¡Tu correo electrónico ha sido verificado! Ahora puedes iniciar sesión.")
            return redirect('accounts:login')
        except User.DoesNotExist:
            messages.error(request, "Usuario no encontrado.")
        except User.MultipleObjectsReturned:
            # Si hay múltiples usuarios (caso improbable), verificar solo el más reciente
            users = User.objects.filter(email=email).order_by('-date_joined')
            latest_user = users.first()
            latest_user.is_verified = True
            latest_user.save()
            
            messages.success(request, "¡Tu correo electrónico ha sido verificado! Ahora puedes iniciar sesión.")
            return redirect('accounts:login')
    else:
        messages.error(request, "El enlace de verificación es inválido o ha expirado.")
    
    return redirect('home')  # Asegúrate de que 'home' sea una URL válida

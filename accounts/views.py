from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from .forms import UserLoginForm, VerificationForm
from django.contrib.auth.decorators import login_required
from .forms import UserRegistrationForm, UserUpdateForm
from django.utils import timezone
from datetime import timedelta
import random
import string
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings
from django.urls import reverse
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
                
                # Si el usuario no está verificado, redirigirlo a la página de verificación
                if not user.is_verified:
                    messages.warning(request, "Por favor verifica tu cuenta para acceder a todas las funcionalidades.")
                    return redirect('accounts:verify')
                
                messages.success(request, "Has iniciado sesión correctamente.")
                return redirect('home')
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
    return redirect('home')

import re

def register_view(request):
    """
    Vista para el registro de nuevos usuarios
    """
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        
        # Obtener la contraseña ingresada
        password1 = request.POST.get('password1', '')
        
        # Validar requisitos de contraseña
        password_errors = []
        
        if len(password1) < 8:
            password_errors.append('La contraseña debe tener al menos 8 caracteres.')
        
        if not re.search(r'[A-Z]', password1):
            password_errors.append('La contraseña debe contener al menos una letra mayúscula.')
        
        if not re.search(r'[a-z]', password1):
            password_errors.append('La contraseña debe contener al menos una letra minúscula.')
        
        if not re.search(r'[!@#$%^&*(),.?":{}|<>_\-+=\[\]\\\/;\'`~]', password1):
            password_errors.append('La contraseña debe contener al menos un símbolo (ej: !@#$%^&*).')
        
        # Si hay errores de validación de contraseña, agregarlos al formulario
        if password_errors:
            for error in password_errors:
                form.add_error('password1', error)
            return render(request, 'accounts/register.html', {'form': form})
        
        # Si pasa las validaciones personalizadas, continuar con el proceso normal
        if form.is_valid():
            user = form.save(commit=False)
            
            # Generar código de verificación
            verification_code = ''.join(random.choices(string.digits, k=6))
            user.verification_code = verification_code
            user.code_expiry = timezone.now() + timedelta(hours=24)
            user.is_verified = False
            user.save()
            
            # Enviar correo con código de verificación
            try:
                send_verification_email(request, user, verification_code)
            except Exception as e:
                # Manejo de error si falla el envío de correo (opcional)
                messages.warning(request, "Error enviando el correo. Contacte soporte.")
            user.backend = 'django.contrib.auth.backends.ModelBackend'
            # Iniciar sesión automáticamente
            login(request, user)
            messages.success(request, "Registro exitoso. Por favor verifica tu correo electrónico.")
            return redirect('accounts:verify')
            
        else:
            # Si el formulario NO es válido, los errores ya están dentro de 'form'
            # y se mostrarán automáticamente en el HTML gracias a {{ field.errors }}
            messages.error(request, "Por favor corrige los errores en el formulario.")
    else:
        form = UserRegistrationForm()
    
    return render(request, 'accounts/register.html', {'form': form})

@login_required
def profile_view(request):
    """
    Vista para el perfil de usuario
    """
    # Si el usuario no está verificado, redirigirlo a la página de verificación
    if not request.user.is_verified:
        messages.warning(request, "Por favor verifica tu cuenta para acceder a todas las funcionalidades.")
        return redirect('accounts:verify')
    
    if request.method == 'POST':
        form = UserUpdateForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Tu perfil ha sido actualizado exitosamente.")
            return redirect('home')
    else:
        form = UserUpdateForm(instance=request.user)
    
    return render(request, 'accounts/profile.html', {'form': form})

@login_required
def verify_account_view(request):
    """
    Vista para verificar la cuenta con código
    """
    user = request.user
    
    # Si el usuario ya está verificado, redirigir al home
    if user.is_verified:
        messages.info(request, "Tu cuenta ya está verificada.")
        return redirect('home')
    
    if request.method == 'POST':
        form = VerificationForm(request.POST)
        if form.is_valid():
            entered_code = form.cleaned_data['verification_code']
            
            # Verificar si el código ha expirado
            if user.code_expiry and user.code_expiry < timezone.now():
                messages.error(request, "El código de verificación ha expirado. Se ha enviado un nuevo código.")
                
                # Generar nuevo código
                new_verification_code = ''.join(random.choices(string.digits, k=6))
                user.verification_code = new_verification_code
                user.code_expiry = timezone.now() + timedelta(hours=24)
                user.save()
                
                # Enviar nuevo código por correo
                send_verification_email(request, user, new_verification_code)
                
                return redirect('accounts:verify')
            
            # Verificar si el código es correcto
            if user.verification_code and user.verification_code == entered_code:
                user.is_verified = True
                user.verification_code = None  # Limpiar el código después de verificar
                user.code_expiry = None  # Limpiar la fecha de expiración
                user.save()
                
                # Enviar correo de bienvenida al usuario
                send_welcome_email(request, user)
                
                messages.success(request, "¡Tu cuenta ha sido verificada exitosamente!")
                return redirect('home')
            else:
                messages.error(request, "Código de verificación incorrecto. Inténtalo de nuevo.")
    else:
        form = VerificationForm()
    
    return render(request, 'accounts/verify.html', {'form': form})

def send_welcome_email(request, user):
    """
    Envía un correo de bienvenida al usuario después de verificar su cuenta
    """
    site_name = request.get_host() if request else 'DECORACIONESMORI'
    domain = request.get_host() if request else 'decoracionesmori.com'
    
    context = {
        'user': user,
        'site_name': site_name,
        'domain': domain,
    }
    
    # Renderiza el correo en formato texto y HTML
    text_content = render_to_string('account/email/welcome_message.txt', context)
    html_content = render_to_string('account/email/welcome_message.html', context)
    
    # Crea el mensaje de correo
    subject = f'¡Bienvenido a {site_name}!'
    from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@decoracionesmori.com')
    to_email = user.email
    
    # Crea el objeto EmailMultiAlternatives para enviar tanto texto como HTML
    msg = EmailMultiAlternatives(subject, text_content, from_email, [to_email])
    msg.attach_alternative(html_content, "text/html")
    
    # Envía el correo
    msg.send()

@login_required
def resend_verification_code(request):
    """
    Vista para reenviar el código de verificación
    """
    user = request.user
    
    # Si el usuario ya está verificado, redirigir al home
    if user.is_verified:
        messages.info(request, "Tu cuenta ya está verificada.")
        return redirect('home')
    
    # Generar nuevo código
    verification_code = ''.join(random.choices(string.digits, k=6))
    user.verification_code = verification_code
    user.code_expiry = timezone.now() + timedelta(hours=24)
    user.save()
    
    # Enviar nuevo código por correo
    send_verification_email(request, user, verification_code)
    
    messages.success(request, "Se ha enviado un nuevo código de verificación a tu correo electrónico.")
    return redirect('accounts:verify')

def send_verification_email(request, user, verification_code):
    """
    Función para enviar el correo de verificación
    """
    site_name = request.get_host() if request else 'DECORACIONESMORI'
    domain = request.get_host() if request else 'decoracionesmori.com'
    
    context = {
        'user': user,
        'site_name': site_name,
        'domain': domain,
        'verification_code': verification_code,
    }
    
    # Renderiza el correo en formato texto y HTML
    text_content = render_to_string('account/email/verification_message.txt', context)
    html_content = render_to_string('account/email/verification_message.html', context)
    
    # Crea el mensaje de correo
    subject = f'Código de verificación para {site_name}'
    from_email = 'noreply@decoracionesmori.com'  # Configura esto en settings.py
    to_email = user.email
    
    # Crea el objeto EmailMultiAlternatives para enviar tanto texto como HTML
    msg = EmailMultiAlternatives(subject, text_content, from_email, [to_email])
    msg.attach_alternative(html_content, "text/html")
    
    # Envía el correo
    msg.send()
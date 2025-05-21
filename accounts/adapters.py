import random
import string
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta
from django.contrib.sites.shortcuts import get_current_site
from django.contrib import messages

class CustomSocialAccountAdapter(DefaultSocialAccountAdapter):
    def save_user(self, request, sociallogin, form=None):
        """
        Guarda el usuario y envía el correo de verificación con código
        """
        # Primero guardamos el usuario normalmente
        user = super().save_user(request, sociallogin, form)
        
        # Generamos un código de verificación
        verification_code = self.generate_verification_code()
        
        # Guardamos el código en el usuario
        user.verification_code = verification_code
        user.code_expiry = timezone.now() + timedelta(hours=24)
        user.is_verified = False  # Marcamos como no verificado
        user.save()
        
        # Ahora enviamos el correo de verificación
        self.send_verification_email(request, user, verification_code)
        
        # Añadimos un mensaje para el usuario
        if request:
            messages.info(request, "Se ha enviado un código de verificación a tu correo electrónico.")
        
        return user
    
    def generate_verification_code(self, length=6):
        """
        Genera un código de verificación aleatorio
        """
        # Generamos un código numérico de 6 dígitos
        return ''.join(random.choices(string.digits, k=length))
    
    def send_verification_email(self, request, user, verification_code):
        """
        Envía un correo con el código de verificación
        """
        current_site = get_current_site(request) if request else None
        site_name = current_site.name if current_site else 'DECORACIONESMORI'
        domain = current_site.domain if current_site else 'decoracionesmori.com'
        
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
        from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@decoracionesmori.com')
        to_email = user.email
        
        # Crea el objeto EmailMultiAlternatives para enviar tanto texto como HTML
        msg = EmailMultiAlternatives(subject, text_content, from_email, [to_email])
        msg.attach_alternative(html_content, "text/html")
        
        # Envía el correo
        msg.send()
    
    def send_welcome_email(self, request, user):
        """
        Envía un correo de bienvenida al usuario después de verificar su cuenta
        """
        current_site = get_current_site(request) if request else None
        site_name = current_site.name if current_site else 'DECORACIONESMORI'
        domain = current_site.domain if current_site else 'decoracionesmori.com'
        
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
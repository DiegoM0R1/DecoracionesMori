# callbacks.py en tu app de accounts
from django.dispatch import receiver
from allauth.socialaccount.signals import social_account_updated, pre_social_login, social_account_added
from django.contrib.auth import get_user_model
from django.shortcuts import redirect
from django.urls import reverse
from django.contrib import messages

User = get_user_model()

@receiver(social_account_added)
def on_social_account_added(request, sociallogin, **kwargs):
    """
    Callback que se ejecuta cuando se añade una cuenta social
    """
    user = sociallogin.user
    
    # Si el usuario no está verificado, redirigir a la página de verificación
    if not user.is_verified:
        messages.info(request, "Por favor verifica tu cuenta para continuar.")
        return redirect('accounts:verify')

@receiver(pre_social_login)
def on_pre_social_login(request, sociallogin, **kwargs):
    """
    Callback que se ejecuta antes de que un usuario inicie sesión con una cuenta social
    """
    user = sociallogin.user
    
    # Si el usuario ya existe y no está verificado, redirigir a la página de verificación
    if user.id and not user.is_verified:
        messages.info(request, "Por favor verifica tu cuenta para continuar.")
        return redirect('accounts:verify')
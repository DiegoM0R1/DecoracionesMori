from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
import dns.resolver

User = get_user_model()

class UserLoginForm(forms.Form):
    """
    Formulario de login para usuarios
    """
    username = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={
            'class': 'form-control', 
            'placeholder': 'Nombre de usuario'
        })
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control', 
            'placeholder': 'Contraseña'
        })
    )

    def clean(self):
        """
        Validaciones adicionales del formulario
        """
        cleaned_data = super().clean()
        username = cleaned_data.get('username')
        password = cleaned_data.get('password')

        # Validaciones personalizadas si son necesarias
        if not username or not password:
            raise ValidationError("Debe ingresar nombre de usuario y contraseña")
        
        return cleaned_data

class UserRegistrationForm(UserCreationForm):
    """
    Formulario de registro para usuarios
    """
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Correo electrónico'
        })
    )           

    class Meta:
        model = User
        fields = [
            'username', 
            'email', 
            'password1', 
            'password2'
        ]
        widgets = {
            'username': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nombre de usuario'
            }),
        }
    
    def clean_email(self):
        """
        Validar que el correo sea único y que exista
        """
        email = self.cleaned_data.get('email')
        
        # Verificar que el correo no esté en uso
        if User.objects.filter(email=email).exists():
            raise ValidationError("Este correo electrónico ya está registrado.")
        
        # Validaciones específicas para proveedores conocidos
        username, domain = email.split('@')
        
        # Validaciones para Gmail
        if domain.lower() == 'gmail.com':
            # Gmail no permite puntos en el nombre de usuario para registros
            # pero los considera iguales
            username_no_dots = username.replace('.', '')
            
            # Gmail no permite nombres de usuario menores a 6 caracteres
            if len(username_no_dots) < 6:
                raise ValidationError("Las direcciones de Gmail deben tener al menos 6 caracteres antes del @.")
            
            # Gmail no permite caracteres especiales excepto puntos
            if not all(c.isalnum() or c == '.' for c in username):
                raise ValidationError("Las direcciones de Gmail solo pueden contener letras, números y puntos.")
        
        # Validaciones para Hotmail/Outlook
        elif domain.lower() in ['hotmail.com', 'outlook.com', 'live.com']:
            if len(username) < 5:
                raise ValidationError("Las direcciones de Microsoft deben tener al menos 5 caracteres antes del @.")
        
        # Verificar que el dominio del correo exista
        try:
            # Verificar si el dominio tiene registros MX válidos (servidor de correo)
            dns.resolver.resolve(domain, 'MX')
        except Exception:
            raise ValidationError(
                "El dominio del correo no parece ser válido. Por favor, utilice un correo electrónico existente."
            )
        
        # Validación adicional: dominios de correo temporales o desechables
        disposable_domains = [
            'tempmail.com', 'temp-mail.org', 'throwawaymail.com', 'mailinator.com',
            'trashmail.com', 'yopmail.com', 'sharklasers.com', 'guerrillamail.com'
        ]
        
        if domain.lower() in disposable_domains:
            raise ValidationError("No se permiten correos electrónicos temporales o desechables.")
            
        return email
      
    def save(self, commit=True):
        """
        Guardar usuario con email y desactivarlo hasta verificación
        """
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.is_active = False  # Desactivar hasta verificación
        
        if commit:
            user.save()
        return user
    
    def send_verification_email(self, user, request):  # Añade el parámetro request
        """
        Enviar correo de verificación
        """
        # Generar token único
        from django.utils.crypto import get_random_string
        from django.urls import reverse
        from django.conf import settings
        import uuid
        
        token = uuid.uuid4().hex
        
        # Guardar token en algún lugar
        from django.core.cache import cache
        cache_key = f"email_verification_{user.email}"
        cache.set(cache_key, token, timeout=86400)  # 24 horas
        
        # Crear URL de verificación con namespace
        verification_url = f"{settings.SITE_URL or request.build_absolute_uri('/').rstrip('/')}{reverse('accounts:verify_email', kwargs={'email': user.email, 'token': token})}"
        
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
        
        # Si tienes request, puedes usar messages
        if request:
            from django.contrib import messages
            messages.success(request, f"Se ha enviado un correo de verificación a {user.email}")
        
        print(f"Correo de verificación enviado a {user.email} con token {token}")

# Añade esto a forms.py
class UserUpdateForm(forms.ModelForm):
    """
    Formulario para actualizar información de perfil de usuario
    """
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Correo electrónico'
        })
    )

    class Meta:
        model = User
        fields = [
            'username', 
            'email', 
            'first_name', 
            'last_name',
            'phone_number',
            'address',
            'dni'
        ]
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-control'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'dni': forms.TextInput(attrs={'class': 'form-control'})
        }

    def clean_email(self):
        """
        Validación de email único
        """
        email = self.cleaned_data.get('email')
        # Excluir el usuario actual de la validación
        qs = User.objects.exclude(pk=self.instance.pk).filter(email=email)
        if qs.exists():
            raise forms.ValidationError('Este correo electrónico ya está en uso')
        return email
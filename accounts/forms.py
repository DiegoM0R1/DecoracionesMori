from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
import re

User = get_user_model()

class UserLoginForm(forms.Form):
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
        cleaned_data = super().clean()
        username = cleaned_data.get('username')
        password = cleaned_data.get('password')
        if not username or not password:
            raise ValidationError("Debe ingresar nombre de usuario y contraseña")
        return cleaned_data

class UserRegistrationForm(UserCreationForm):
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Correo electrónico'
        })
    )
    
    # Redefinimos los campos de contraseña para asegurar que usen tus widgets
    password1 = forms.CharField(
        label="Contraseña",
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Contraseña'
        })
    )
    password2 = forms.CharField(
        label="Confirmar contraseña",
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Confirmar contraseña'
        })
    )

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']
        widgets = {
            'username': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nombre de usuario'
            }),
        }
    
    # 1. VALIDACIÓN DE USUARIO (Esto soluciona tu problema principal)
    def clean_username(self):
        username = self.cleaned_data.get('username')
        
        # 1. Unicidad (Más formal)
        if User.objects.filter(username=username).exists():
            raise ValidationError("El nombre de usuario ingresado no está disponible.")
        
        # 2. Longitud mínima (Más preciso)
        if len(username) < 4:
            raise ValidationError("El nombre de usuario debe contener un mínimo de 4 caracteres.")
            
        # 3. Solo números (Más técnico)
        if username.isdigit():
             raise ValidationError("El nombre de usuario no puede estar compuesto exclusivamente por caracteres numéricos.")

        # 4. Caracteres permitidos (Explicativo)
        if not re.match(r'^[a-zA-Z0-9_.]+$', username):
             raise ValidationError("El formato del nombre de usuario es inválido. Solo se permiten letras, números, puntos (.) y guiones bajos (_).")
        
        username = self.cleaned_data.get('username')
        if User.objects.filter(username=username).exists():
            raise ValidationError("Este nombre de usuario ya está en uso. Por favor elige otro.")
        return username

    # 2. VALIDACIÓN DE EMAIL
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise ValidationError('Este correo electrónico ya está registrado.')
        return email

    # 3. VALIDACIÓN DE CONTRASEÑA (Movido desde views.py para mayor seguridad)
    def clean_password1(self):
        password = self.cleaned_data.get('password1')
        
        errors = []
        if len(password) < 8:
            errors.append('La contraseña debe tener al menos 8 caracteres.')
        if not re.search(r'[A-Z]', password):
            errors.append('La contraseña debe contener al menos una letra mayúscula.')
        if not re.search(r'[a-z]', password):
            errors.append('La contraseña debe contener al menos una letra minúscula.')
        if not re.search(r'[!@#$%^&*(),.?":{}|<>_\-+=\[\]\\\/;\'`~]', password):
            errors.append('La contraseña debe contener al menos un símbolo.')

        if errors:
            raise ValidationError(errors)
            
        return password

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        # En UserCreationForm, la contraseña se setea automáticamente, 
        # pero como estamos redefiniendo save, nos aseguramos.
        user.set_password(self.cleaned_data["password1"])
        if commit:
            user.save()
        return user

class UserUpdateForm(forms.ModelForm):
    # ... (El resto de tus formularios se mantiene igual)
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Correo electrónico'
        })
    )

    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'phone_number', 'address', 'dni']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-control'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'dni': forms.TextInput(attrs={'class': 'form-control'})
        }

    def clean_email(self):
        email = self.cleaned_data.get('email')
        qs = User.objects.exclude(pk=self.instance.pk).filter(email=email)
        if qs.exists():
            raise forms.ValidationError('Este correo electrónico ya está en uso')
        return email

class VerificationForm(forms.Form):
    verification_code = forms.CharField(
        label='Código de verificación',
        max_length=6,
        min_length=6,
        widget=forms.TextInput(attrs={
            'class': 'form-control text-center',
            'placeholder': 'Ingresa el código de 6 dígitos',
            'style': 'letter-spacing: 5px; font-size: 24px;'
        })
    )
    
    def clean_verification_code(self):
        code = self.cleaned_data.get('verification_code')
        if not code.isdigit():
            raise forms.ValidationError('El código de verificación debe contener solo números')
        return code
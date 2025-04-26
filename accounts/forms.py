from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError

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
            'password1': forms.PasswordInput(attrs={
                'class': 'form-control',
                'placeholder': 'Contraseña'
            }),
            'password2': forms.PasswordInput(attrs={
                'class': 'form-control',
                'placeholder': 'Confirmar contraseña'
            })
        }
    
        def save(self, commit=True):
            """
            Guardar usuario con email
            """
            user = super().save(commit=False)
            user.email = self.cleaned_data['email']
            
            if commit:
                user.save()
            return user
    
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
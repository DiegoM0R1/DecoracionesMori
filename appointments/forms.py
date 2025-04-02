# appointments/forms.py
from django import forms
from django.utils.translation import gettext_lazy as _
from .models import Appointment, StaffAvailability
from services.models import Service
from accounts.models import User

class AppointmentRequestForm(forms.ModelForm):
    name = forms.CharField(
        max_length=100, 
        widget=forms.TextInput(attrs={
            'class': 'form-control', 
            'placeholder': 'Nombre completo'
        })
    )
    dni = forms.CharField(
        max_length=20, 
        label='DNI',
        widget=forms.TextInput(attrs={
            'class': 'form-control', 
            'placeholder': 'Número de documento'
        })
    )
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'form-control', 
            'placeholder': 'Correo electrónico'
        })
    )
    phone_number = forms.CharField(
        max_length=15, 
        widget=forms.TextInput(attrs={
            'class': 'form-control', 
            'placeholder': 'Teléfono de contacto'
        })
    )
    address = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'placeholder': 'Dirección completa',
            'rows': 3
        })
    )
    preferred_date = forms.DateField(
        widget=forms.DateInput(attrs={
            'type': 'date', 
            'class': 'form-control'
        })
    )
    preferred_time = forms.ChoiceField(
        choices=[
            ('', _('Selecciona un horario')),
            ('morning', _('Mañana (9:00 - 12:00)')),
            ('afternoon', _('Tarde (13:00 - 17:00)')),
        ],
        widget=forms.Select(attrs={'class': 'form-select'}),
        required=False
    )

    class Meta:
        model = Appointment
        fields = ['service', 'notes']
        widgets = {
            'service': forms.HiddenInput(),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Información adicional (opcional)',
                'rows': 3
            })
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Si se pasa un servicio inicial, configura el campo de servicio
        if 'initial' in kwargs and 'service' in kwargs['initial']:
            self.fields['service'].initial = kwargs['initial']['service']
    
    def clean(self):
        cleaned_data = super().clean()
        
        # Make sure all required fields are present
        required_fields = ['name', 'dni', 'email', 'phone_number', 'address', 'preferred_date']
        for field in required_fields:
            if field not in cleaned_data or not cleaned_data[field]:
                self.add_error(field, _('Este campo es obligatorio'))
        
        return cleaned_data
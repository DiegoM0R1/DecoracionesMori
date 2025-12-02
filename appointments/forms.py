# appointments/forms.py
from django import forms
from django.utils.translation import gettext_lazy as _
from .models import Appointment, ScheduledWorkDay
from services.models import Service
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.contrib.auth import get_user_model
import datetime

User = get_user_model()


class AppointmentRequestForm(forms.ModelForm):
    TIPO_CLIENTE_CHOICES = [
        ('persona', 'Persona (DNI)'),
        ('empresa', 'Empresa (RUC)'),
    ]
    client_type = forms.ChoiceField(
        choices=TIPO_CLIENTE_CHOICES,
        widget=forms.RadioSelect(attrs={'class': 'btn-check', 'autocomplete': 'off'}),
        initial='persona',
        label=_("Tipo de Cliente")
    )
    # Campos para obtener datos del cliente
    # 1. CAMBIO DE ORDEN: DNI ahora está antes de 'name'
    dni = forms.CharField(
        label=_("DNI"),
        max_length=20, # Coincide con User.dni
        required=False, # El DNI puede ser opcional
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('Tu número de documento')})
    )
    # --- NUEVOS CAMPOS PARA EMPRESA ---
    ruc = forms.CharField(
        label=_("RUC"), max_length=11, required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ingresa el RUC de la empresa'})
    )
    razon_social = forms.CharField(
        label=_("Razón Social"), max_length=200, required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'readonly': 'readonly'})
    )
    name = forms.CharField(
        label=_("Nombre Completo"),
        max_length=100, # Coincide con first_name + last_name aprox.
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('Tu nombre completo (se autocompleta con DNI)')}) # Placeholder actualizado
    )
    email = forms.EmailField(
        label=_("Correo Electrónico"), # Para usuarios autenticados, este campo será oculto
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': _('Tu correo electrónico')})
    )
    phone_number = forms.CharField(
        label=_("Teléfono"),
        max_length=15, # Coincide con User.phone_number
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('Tu teléfono de contacto')})
    )
    address = forms.CharField(
        label=_("Dirección"),
        required=False,
        widget=forms.TextInput(attrs={ # <--- CAMBIADO A TextInput
        'class': 'form-control', 
        'placeholder': _('Empieza a escribir tu dirección...'), 
        'id': 'id_address_input' # Asegúrate de que tenga este ID
    })
)

    # Campos del modelo Appointment (sin cambios en su declaración aquí)
    appointment_date = forms.DateField(
        label=_("Fecha Preferida"),
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control', 'id': 'id_appointment_date_form'}),
    )
    appointment_time = forms.TimeField(
        label=_("Hora Preferida"),
        widget=forms.TimeInput(attrs={'type': 'time', 'class': 'form-control', 'id': 'id_appointment_time_form'})
    )
    
    nombres_hidden = forms.CharField(widget=forms.HiddenInput(), required=False)
    apellido_paterno_hidden = forms.CharField(widget=forms.HiddenInput(), required=False)
    apellido_materno_hidden = forms.CharField(widget=forms.HiddenInput(), required=False)

    class Meta:
        model = Appointment
        fields = ['service', 'appointment_date', 'appointment_time', 'notes']
        widgets = {
            'service': forms.HiddenInput(),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': _('Información adicional sobre tu cita (opcional)'),
                'rows': 3
            }),
        }
        labels = {
            'notes': _('Notas Adicionales'),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        self.service_id = kwargs.pop('service_id', None)
        
        # Obtenemos los valores iniciales que puedan venir de la vista
        initial = kwargs.get('initial', {})

        # --- LÓGICA DE AUTOCOMPLETADO ---
        if self.user and self.user.is_authenticated:
            # 1. Datos de Contacto Comunes (Siempre se llenan)
            initial.setdefault('email', self.user.email)
            initial.setdefault('phone_number', getattr(self.user, 'phone_number', ''))
            initial.setdefault('address', getattr(self.user, 'address', ''))
            
            # 2. Decidir si es EMPRESA o PERSONA basado en los datos guardados
            user_ruc = getattr(self.user, 'ruc', '')
            user_dni = getattr(self.user, 'dni', '')
            
            # Si tiene RUC guardado (y tiene 11 dígitos), asumimos que es EMPRESA
            if user_ruc and len(str(user_ruc).strip()) == 11:
                initial['client_type'] = 'empresa'
                initial['ruc'] = user_ruc
                # En la lógica de guardado anterior, pusimos la Razón Social en first_name
                initial['razon_social'] = self.user.first_name 
                initial['name'] = self.user.first_name # Campo visible compartido
            
            # Si no tiene RUC, asumimos que es PERSONA
            else:
                initial['client_type'] = 'persona'
                if user_dni:
                    initial['dni'] = user_dni
                # Para persona, el nombre es Nombre + Apellido
                initial['name'] = self.user.get_full_name() 

        # Pasamos el diccionario 'initial' actualizado al formulario
        kwargs['initial'] = initial
        super().__init__(*args, **kwargs)

        # --- AJUSTES DE WIDGETS ---
        
        # Si está logueado, ocultamos el email (ya lo tenemos)
        if self.user and self.user.is_authenticated:
            if 'email' in self.fields:
                self.fields['email'].widget = forms.HiddenInput()
        
        # Pre-seleccionar servicio si viene en la URL
        if self.service_id:
            try:
                service = Service.objects.get(pk=self.service_id)
                if 'service' in self.fields: 
                    self.fields['service'].initial = service
            except Service.DoesNotExist:
                pass
        
        # Limpiar campo staff si no hay personal
        if 'staff' in self.fields and not self.fields['staff'].queryset.exists():
            del self.fields['staff']

    def clean_appointment_date(self):
        date = self.cleaned_data.get('appointment_date')
        if date:
            # REGLA 1: No se pueden registrar citas para hoy o días pasados. Mínimo 1 día de antelación.
            # (timezone.now().date() + datetime.timedelta(days=1)) es mañana.
            if date < (timezone.now().date() + datetime.timedelta(days=1)):
                raise ValidationError(
                    _("La fecha de la cita debe ser con al menos un día de antelación (a partir de mañana).")
                )
            
            # Validación de día laborable según ScheduledWorkDay
            try:
                workday = ScheduledWorkDay.objects.get(date=date)
                if not workday.is_working:
                    raise ValidationError(_("La fecha seleccionada no es un día laborable según nuestra programación."))
            except ScheduledWorkDay.DoesNotExist:
                raise ValidationError(
                    _("No hay información de horario laboral para la fecha {date}. Por favor, consulte con el administrador.").format(date=date.strftime("%d/%m/%Y"))
                )
        return date

    def clean_email(self): # Tu lógica existente para el email
        if self.user and self.user.is_authenticated:
            return self.user.email
        email_from_form = self.cleaned_data.get('email')
        if not email_from_form:
            raise ValidationError(_("Se requiere una dirección de correo electrónico."))
        return email_from_form

    def clean(self):
        cleaned_data = super().clean()
        client_type = cleaned_data.get('client_type')
        dni = cleaned_data.get('dni')
        ruc = cleaned_data.get('ruc')

        # Validación condicional
        if client_type == 'persona':
            if not dni:
                self.add_error('dni', _("El DNI es obligatorio para personas."))
            # Limpiamos datos de empresa para evitar basura
            cleaned_data['ruc'] = ''
            cleaned_data['razon_social'] = ''
            
        elif client_type == 'empresa':
            if not ruc:
                self.add_error('ruc', _("El RUC es obligatorio para empresas."))
            if len(ruc) != 11:
                self.add_error('ruc', _("El RUC debe tener 11 dígitos."))
            # Limpiamos datos de persona
            cleaned_data['dni'] = ''
            
        return cleaned_data



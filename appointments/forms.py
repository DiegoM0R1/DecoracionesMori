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
    # Campos para obtener datos del cliente
    # 1. CAMBIO DE ORDEN: DNI ahora está antes de 'name'
    dni = forms.CharField(
        label=_("DNI"),
        max_length=20, # Coincide con User.dni
        required=False, # El DNI puede ser opcional
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('Tu número de documento')})
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
        # ... (tu __init__ existente para user, service_id, initial, ocultar email, etc.) ...
        # Este método __init__ que ya tienes para pre-rellenar datos y ocultar el email
        # para usuarios logueados es correcto y no necesita cambios para estas nuevas reglas.
        self.user = kwargs.pop('user', None)
        self.service_id = kwargs.pop('service_id', None)
        initial = kwargs.get('initial', {})

        if self.user and self.user.is_authenticated:
            initial.setdefault('email', self.user.email)
            initial.setdefault('dni', getattr(self.user, 'dni', ''))
            initial.setdefault('phone_number', getattr(self.user, 'phone_number', ''))
            initial.setdefault('address', getattr(self.user, 'address', ''))
        
        kwargs['initial'] = initial
        super().__init__(*args, **kwargs)

        if self.user and self.user.is_authenticated:
            if 'email' in self.fields:
                self.fields['email'].widget = forms.HiddenInput()
        
        if self.service_id:
            try:
                service = Service.objects.get(pk=self.service_id)
                if 'service' in self.fields: self.fields['service'].initial = service
            except Service.DoesNotExist:
                if 'service' in self.fields: self.fields['service'].queryset = Service.objects.none()
        
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
        appointment_date = cleaned_data.get('appointment_date')
        appointment_time = cleaned_data.get('appointment_time')

        # Si appointment_date ya tuvo un error en su validación individual, no continuar.
        if self.errors.get('appointment_date'):
            return cleaned_data

        # REGLA 2: Límite de 3 citas por día.
        if appointment_date:
            # Contar citas existentes (pendientes o confirmadas) para esa fecha.
            # No contamos la cita actual si se está editando y no cambia de fecha.
            query_filter = Appointment.objects.filter(
                appointment_date=appointment_date,
                status__in=['pending', 'confirmed'] # Solo estas cuentan para el cupo
            )

            # Si estamos editando una cita (self.instance.pk existe), la excluimos del conteo
            # para permitir guardar cambios que no afecten al cupo (ej. cambiar notas).
            if self.instance and self.instance.pk:
                query_filter = query_filter.exclude(pk=self.instance.pk)
            
            existing_appointments_count = query_filter.count()

            if existing_appointments_count >= 3:
                # Formatear la fecha para el mensaje
                # date_formatted = appointment_date.strftime('%d de %B de %Y') # Considera localizar el mes
                self.add_error('appointment_date', ValidationError(
                    _("Lo sentimos, ya no hay cupos disponibles para el día {date}. "
                      "Se permite un máximo de 3 citas diarias.").format(
                        date=appointment_date.strftime("%d/%m/%Y") # Formato simple
                    )
                ))
                # No tiene sentido validar la hora si el día ya está lleno.
                # Pero si se validara, se podría quitar 'appointment_time' de cleaned_data o añadir error.
                # if 'appointment_time' in cleaned_data:
                # del cleaned_data['appointment_time']
                # return cleaned_data # Salir temprano si el día está lleno

        # Validación de hora contra el ScheduledWorkDay (si la fecha es válida y hay hora)
        if appointment_date and appointment_time and not self.errors.get('appointment_date'): # Solo si no hay error previo en fecha
            try:
                workday = ScheduledWorkDay.objects.get(date=appointment_date)
                # workday.is_working ya fue verificado en clean_appointment_date
                if workday.start_time and workday.end_time:
                    if not (workday.start_time <= appointment_time < workday.end_time):
                        self.add_error('appointment_time', ValidationError(
                            _("La hora seleccionada ({time}) está fuera del horario laboral ({start}-{end}) para el día {date}.").format(
                                time=appointment_time.strftime('%H:%M'),
                                start=workday.start_time.strftime('%H:%M'),
                                end=workday.end_time.strftime('%H:%M'),
                                date=appointment_date.strftime('%d/%m/%Y')
                            )
                        ))
                # else: Si el día es laborable pero no tiene start/end time definidos,
                # se podría asumir que cualquier hora es válida o que se maneja de otra forma.
                # Actualmente, si no hay start/end time, no se valida la hora.
            except ScheduledWorkDay.DoesNotExist:
                # Esto ya debería haber sido capturado por clean_appointment_date.
                # No es necesario añadir otro error aquí si clean_appointment_date es robusto.
                pass
        
        return cleaned_data
# appointments/forms.py
from django import forms
from django.utils.translation import gettext_lazy as _
from .models import Appointment, ScheduledWorkDay
from services.models import Service
from django.conf import settings # Para referenciar User model
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.contrib.auth import get_user_model
import datetime

User = get_user_model()
class AppointmentRequestForm(forms.ModelForm):
    # Campos para obtener datos del cliente (si no está logueado o para crear/actualizar)
    # Estos NO son campos del modelo Appointment directamente, se usan en la vista
    name = forms.CharField(label=_("Nombre Completo"), max_length=100, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('Nombre completo')}))
    dni = forms.CharField(label=_("DNI"), max_length=20, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('Número de documento')}))
    email = forms.EmailField(label=_("Correo Electrónico"), widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': _('Correo electrónico')}))
    phone_number = forms.CharField(label=_("Teléfono"), max_length=15, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('Teléfono de contacto')}))
    address = forms.CharField(label=_("Dirección"), required=False, widget=forms.Textarea(attrs={'class': 'form-control', 'placeholder': _('Dirección completa (opcional)'), 'rows': 3}))

    # Campos que SÍ mapean al modelo Appointment (o se usan para él)
    appointment_date = forms.DateField(
        label=_("Fecha Preferida"),
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        # Añadir validador para no permitir fechas pasadas
        validators=[lambda date: date >= timezone.now().date()]
    )
    appointment_time = forms.TimeField(
        label=_("Hora Preferida"),
        widget=forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'})
        # Considera usar un ChoiceField si generas slots específicos en la vista/JS
    )
    # Campo para seleccionar staff (si aplica y quieres que el cliente elija)
    staff = forms.ModelChoiceField(
        label=_("Profesional Preferido (Opcional)"),
        queryset=User.objects.filter(is_staff=True, is_active=True),
        required=False, # Hacerlo opcional si el sistema puede asignar uno
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    class Meta:
        model = Appointment
        # Campos del modelo que se manejarán directamente por el form
        fields = ['service', 'staff', 'appointment_date', 'appointment_time', 'notes']
        widgets = {
            'service': forms.HiddenInput(), # El servicio se obtiene de la URL
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': _('Información adicional (opcional)'),
                'rows': 3
            }),
        }
        labels = {
            'notes': _('Notas Adicionales'),
        }

    def __init__(self, *args, **kwargs):
        # Obtener service_id si se pasa (para inicializar o filtrar)
        self.service_id = kwargs.pop('service_id', None)
        super().__init__(*args, **kwargs)

        if self.service_id:
            try:
                service = Service.objects.get(pk=self.service_id)
                self.fields['service'].initial = service
                # Opcional: Filtrar staff basado en el servicio si tienes esa lógica
                # self.fields['staff'].queryset = User.objects.filter(is_staff=True, is_active=True, services_offered=service)
            except Service.DoesNotExist:
                # Manejar el caso donde el service_id es inválido
                 self.fields['service'].queryset = Service.objects.none() # No mostrar opciones

        # Ocultar el campo 'staff' si no hay staff disponible o si no quieres que el cliente elija
        if not self.fields['staff'].queryset.exists():
             del self.fields['staff']


    def clean_appointment_date(self):
        """Valida si la fecha seleccionada es un día laborable."""
        date = self.cleaned_data.get('appointment_date')
        if date:
            if date < timezone.now().date():
                 raise ValidationError(_("No puedes seleccionar una fecha pasada."))
            try:
                workday = ScheduledWorkDay.objects.get(date=date)
                if not workday.is_working:
                    raise ValidationError(_("La fecha seleccionada no es un día laborable."))
            except ScheduledWorkDay.DoesNotExist:
                 raise ValidationError(_("No hay información de horario para la fecha seleccionada."))
        return date

    def clean(self):
        """Valida la hora contra el horario del día y otras reglas."""
        cleaned_data = super().clean()
        appointment_date = cleaned_data.get('appointment_date')
        appointment_time = cleaned_data.get('appointment_time')
        service = cleaned_data.get('service')
        staff = cleaned_data.get('staff') # Puede ser None si es opcional

        if appointment_date and appointment_time:
            try:
                workday = ScheduledWorkDay.objects.get(date=appointment_date)
                # Validar hora dentro del rango general (si está definido)
                if workday.start_time and workday.end_time:
                    if not (workday.start_time <= appointment_time < workday.end_time):
                        self.add_error('appointment_time', ValidationError(
                            _("La hora seleccionada está fuera del horario laboral general ({start}-{end}) para este día.").format(
                                start=workday.start_time.strftime('%H:%M'),
                                end=workday.end_time.strftime('%H:%M')
                            )
                        ))

                    

            except ScheduledWorkDay.DoesNotExist:
                # Esto ya se valida en clean_appointment_date, pero por si acaso
                self.add_error('appointment_date', _("No hay información de horario para la fecha seleccionada."))

        return cleaned_data
# appointments/models.py
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.conf import settings # Mejor forma de referenciar User model
from services.models import Service # Asumiendo que está en la app 'services'
from django.utils import timezone
import datetime
from django.core.exceptions import ValidationError
# --- Modelos de Horario Laboral ---

class WorkScheduleTemplate(models.Model):
    """
    Define la plantilla estándar para los horarios de trabajo de cada día de la semana.
    (Código idéntico al proporcionado anteriormente)
    """
    DAY_CHOICES = [
        (0, _('Lunes')), (1, _('Martes')), (2, _('Miércoles')),
        (3, _('Jueves')), (4, _('Viernes')), (5, _('Sábado')), (6, _('Domingo')),
    ]
    day_of_week = models.IntegerField(choices=DAY_CHOICES, unique=True, verbose_name=_('Día de la semana'))
    start_time = models.TimeField(verbose_name=_('Hora de inicio'), null=True, blank=True)
    end_time = models.TimeField(verbose_name=_('Hora de fin'), null=True, blank=True)
    is_working_day = models.BooleanField(default=True, verbose_name=_('¿Es día laborable?'))

    class Meta:
        verbose_name = _('Plantilla de Horario Semanal')
        verbose_name_plural = _('Plantillas de Horario Semanal')
        ordering = ['day_of_week']

    def __str__(self):
        day_name = self.get_day_of_week_display()
        if self.is_working_day and self.start_time and self.end_time:
            return f"{day_name}: {self.start_time.strftime('%H:%M')} - {self.end_time.strftime('%H:%M')}"
        elif self.is_working_day:
             return f"{day_name}: {_('Día laborable (sin hora definida)')}"
        else:
            return f"{day_name}: {_('No laborable')}"

class ScheduledWorkDay(models.Model):
    """
    Representa un día específico en el calendario con su horario de trabajo general.
    (Código idéntico al proporcionado anteriormente)
    """
    date = models.DateField(unique=True, verbose_name=_('Fecha'))
    start_time = models.TimeField(verbose_name=_('Hora de inicio general'), null=True, blank=True)
    end_time = models.TimeField(verbose_name=_('Hora de fin general'), null=True, blank=True)
    is_working = models.BooleanField(default=True, verbose_name=_('¿Se trabaja este día?'))
    notes = models.TextField(verbose_name=_('Notas generales del día'), blank=True, null=True)

    class Meta:
        verbose_name = _('Día de Trabajo Programado')
        verbose_name_plural = _('Días de Trabajo Programados')
        ordering = ['date']

    def __str__(self):
        date_str = self.date.strftime('%Y-%m-%d')
        day_name = self.date.strftime('%A') # Considera localizar esto
        if self.is_working and self.start_time and self.end_time:
            return f"{date_str} ({day_name}): {self.start_time.strftime('%H:%M')} - {self.end_time.strftime('%H:%M')}"
        elif self.is_working:
             return f"{date_str} ({day_name}): {_('Se trabaja (sin hora definida)')}"
        else:
            return f"{date_str} ({day_name}): {_('No se trabaja')}"

    @property
    def day_of_week(self):
        return self.date.weekday()

# --- Modelo de Cita Modificado ---

class Appointment(models.Model):
    STATUS_CHOICES = (
        # Considera traducir las claves también o usar constantes
        ("pending", _("Pendiente")),
        ("confirmed", _("Confirmada")),
        ("completed", _("Completada")),
        ("cancelled", _("Cancelada")),
    )

    client = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE, # O SET_NULL si un cliente puede ser borrado pero sus citas quedan registradas
        related_name="client_appointments", # Cambiado para evitar conflicto con staff
        verbose_name=_("Cliente")
    )
    service = models.ForeignKey(
        Service,
        on_delete=models.CASCADE, # O SET_NULL si prefieres mantener la cita si se borra el servicio
        related_name="appointments",
        verbose_name=_("Servicio")
    )
    # NUEVO: Enlace al personal (asumiendo que tu User model tiene 'is_staff')
    staff = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True, # Permitir citas sin asignar personal inicialmente?
        related_name="staff_appointments",
        limit_choices_to={'is_staff': True}, # Solo permite seleccionar usuarios que sean staff
        verbose_name=_("Personal Asignado")
    )
    # NUEVO: Fecha y hora específicas de la cita
    appointment_date = models.DateField(
        verbose_name=_("Fecha de la Cita"),
        null=True,  # Permite nulos en la BD
        blank=True  # Permite que el campo esté vacío en formularios/admin

    )
    appointment_time = models.TimeField(
        verbose_name=_("Hora de la Cita"),
        null=True,
        blank=True
    )

    # ELIMINADO: staff_availability = models.ForeignKey(StaffAvailability, on_delete=models.SET_NULL, null=True)

    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Fecha de Creación"))
    status = models.CharField(
        _("Estado"),
        max_length=20,
        choices=STATUS_CHOICES,
        default="pending"
    )
    notes = models.TextField(_("Notas del Cliente"), blank=True)

    class Meta:
        db_table = 'citas' # Nombre de tabla en español
        verbose_name = _("Cita")
        verbose_name_plural = _("Citas")
        ordering = ['-appointment_date', '-appointment_time'] # Ordenar por fecha/hora de cita

    def __str__(self):
        client_name = self.client.get_full_name() or self.client.username
        service_name = self.service.name
        date_str = self.appointment_date.strftime('%d/%m/%Y')
        time_str = self.appointment_time.strftime('%H:%M')
        return f"Cita para {client_name} - {service_name} el {date_str} a las {time_str} ({self.get_status_display()})"

    def clean(self):
        """
        Validaciones personalizadas.
        """
        super().clean()
        # Validar que la hora de la cita esté dentro del horario laboral del día programado
        # Solo validar si hay fecha asignada
        if self.appointment_date:
            try:
                workday = ScheduledWorkDay.objects.get(date=self.appointment_date)
                if not workday.is_working:
                    # Usa ValidationError directamente (importado arriba)
                    raise ValidationError(
                        _("La fecha seleccionada ({date}) no es un día laborable.").format(date=self.appointment_date)
                    )
                # Solo validar hora si hay hora en la cita y horario definido en el día
                if self.appointment_time and workday.start_time and workday.end_time:
                    if not (workday.start_time <= self.appointment_time < workday.end_time):
                        # Usa ValidationError directamente y asócialo al campo
                        raise ValidationError({
                            'appointment_time': _("La hora seleccionada ({time}) está fuera del horario laboral ({start}-{end}) para el día {date}.").format(
                                time=self.appointment_time.strftime('%H:%M'),
                                start=workday.start_time.strftime('%H:%M'),
                                end=workday.end_time.strftime('%H:%M'),
                                date=self.appointment_date
                            )
                        })
                # --- Aquí irían otras validaciones si las necesitas (conflictos, etc.) ---

            except ScheduledWorkDay.DoesNotExist:
                 # Usa ValidationError directamente y asócialo al campo
                 # con el mensaje CORRECTO para esta excepción
                raise ValidationError({
                    'appointment_date': _("No hay información de horario laboral para la fecha seleccionada ({date}). Contacte al administrador.").format(date=self.appointment_date)
                })

    # Considera añadir métodos para obtener la fecha/hora formateadas si lo necesitas a menudo
    # def get_formatted_date(self):
    #     return self.appointment_date.strftime('%d/%m/%Y')

    # def get_formatted_time(self):
    #     return self.appointment_time.strftime('%H:%M')
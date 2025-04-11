from django.db import models
from django.utils.translation import gettext_lazy as _
from accounts.models import User
from services.models import Service

class StaffAvailability(models.Model):
    staff = models.ForeignKey(User, on_delete=models.CASCADE, limit_choices_to={"is_staff": True})
    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    is_available = models.BooleanField(default=True)
    
    class Meta:
        db_table = 'disponibilidad_personal'  # Nombre de la tabla en español
        verbose_name = _("Staff Availability")
        verbose_name_plural = _("Staff Availabilities")
        unique_together = ("staff", "date", "start_time")
    
    def __str__(self):
        return f"{self.staff.username} - {self.date} ({self.start_time}-{self.end_time})"

class Appointment(models.Model):
    STATUS_CHOICES = (
        ("pending", _("Pending")),
        ("confirmed", _("Confirmed")),
        ("completed", _("Completed")),
        ("cancelled", _("Cancelled")),
    )
    
    client = models.ForeignKey(User, on_delete=models.CASCADE, related_name="appointments")
    service = models.ForeignKey(Service, on_delete=models.CASCADE, related_name="appointments")
    staff_availability = models.ForeignKey(StaffAvailability, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(_("Status"), max_length=20, choices=STATUS_CHOICES, default="pending")
    notes = models.TextField(_("Notes"), blank=True)
    
    class Meta:
        db_table = 'cita'  # Nombre de la tabla en español
        verbose_name = _("Appointment")
        verbose_name_plural = _("Appointments")
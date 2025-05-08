# clients/models.py
from django.db import models
from django.conf import settings # Para AUTH_USER_MODEL
from django.utils.translation import gettext_lazy as _

class ClientProfile(models.Model):
    CLIENT_TYPE_CHOICES = [
        ('prospect', _('Prospecto')),
        ('active', _('Activo')),
        ('inactive', _('Inactivo')),
    ]

    # Enlace UNO-A-UNO con tu modelo User. Cada User no-staff tendrá UN ClientProfile.
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='client_profile',
        verbose_name=_("Usuario")
        # limit_choices_to={'is_staff': False} # Ayuda en el admin al seleccionar
    )

    client_type = models.CharField(
        _("Tipo de cliente"),
        max_length=20,
        choices=CLIENT_TYPE_CHOICES,
        default='prospect', # O el que prefieras
    )
    # NO necesitas duplicar aquí nombre, DNI, email, etc. Se accederán desde 'user'.

    class Meta:
        verbose_name = _("Cliente")
        verbose_name_plural = _("Clientes")

    def __str__(self):
        # Cómo se verá el cliente en el admin y otros lugares
        return self.user.get_full_name() or self.user.username
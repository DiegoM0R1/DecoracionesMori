from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.translation import gettext_lazy as _

class User(AbstractUser):
    phone_number = models.CharField(_("Phone number"), max_length=15, blank=True)
    address = models.TextField(_("Address"), blank=True)
    dni = models.CharField(_("DNI"), max_length=20, blank=True)
    is_verified = models.BooleanField(_("Is verified"), default=False)
    
    groups = models.ManyToManyField(
        'auth.Group',
        related_name='custom_user_set',  # Change this to a unique related name
        blank=True,
        help_text='The groups this user belongs to.',
        verbose_name='groups',
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        related_name='custom_user_set',  # Change this to a unique related name
        blank=True,
        help_text='Specific permissions for this user.',
        verbose_name='user permissions',
    )
    class Meta:
        db_table = 'usuario'  # Nombre de la tabla en español
        verbose_name = _("User")
        verbose_name_plural = _("Users")

# 1. models.py
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.translation import gettext_lazy as _

class User(AbstractUser):
    """
    Modelo de usuario personalizado para Allauth
    """ 
    phone_number = models.CharField(_("Phone number"), max_length=15, blank=True)
    address = models.TextField(_("Address"), blank=True)
    dni = models.CharField(_("DNI"), max_length=20, blank=True)
    is_verified = models.BooleanField(_("Is verified"), default=False)
    
    groups = models.ManyToManyField(
        'auth.Group',
        related_name='custom_user_set',
        blank=True,
        help_text=_('The groups this user belongs to.'),
        verbose_name=_('groups'),
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        related_name='custom_user_set',
        blank=True,
        help_text=_('Specific permissions for this user.'),
        verbose_name=_('user permissions'),
    )
    
    class Meta:
        db_table = 'usuario'
        verbose_name = _("User")
        verbose_name_plural = _("Users")
    
    def __str__(self):
        return f"{self.username} - {self.get_full_name()}"
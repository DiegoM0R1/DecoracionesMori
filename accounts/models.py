# accounts/models.py
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.translation import gettext_lazy as _

class User(AbstractUser):
    phone_number = models.CharField(_("Phone number"), max_length=15, blank=True)
    address = models.TextField(_("Address"), blank=True)
    dni = models.CharField(_("DNI"), max_length=20, blank=True)
    is_verified = models.BooleanField(_("Is verified"), default=False)

    class Meta:
        verbose_name = _("User")
        verbose_name_plural = _("Users")


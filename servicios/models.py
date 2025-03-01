# Create your models here.
from django.db import models
from django.utils.translation import gettext_lazy as _

class ServiceCategory(models.Model):
    name = models.CharField(_("Name"), max_length=100)
    description = models.TextField(_("Description"), blank=True)
    
    class Meta:
        verbose_name = _("Service Category")
        verbose_name_plural = _("Service Categories")
    
    def __str__(self):
        return self.name

class Service(models.Model):
    category = models.ForeignKey(ServiceCategory, on_delete=models.CASCADE, related_name="services")
    name = models.CharField(_("Name"), max_length=100)
    description = models.TextField(_("Description"))
    base_price = models.DecimalField(_("Base Price"), max_digits=10, decimal_places=2)
    is_active = models.BooleanField(_("Is active"), default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _("Service")
        verbose_name_plural = _("Services")
    
    def __str__(self):
        return self.name

class ServiceImage(models.Model):
    service = models.ForeignKey(Service, on_delete=models.CASCADE, related_name="images")
    image = models.ImageField(_("Image"), upload_to="services/")
    is_featured = models.BooleanField(_("Is featured"), default=False)
    
    class Meta:
        verbose_name = _("Service Image")
        verbose_name_plural = _("Service Images")

class ServiceVideo(models.Model):
    service = models.ForeignKey(Service, on_delete=models.CASCADE, related_name="videos")
    video = models.FileField(_("Video"), upload_to="services/videos/")
    title = models.CharField(_("Title"), max_length=100)
    
    class Meta:
        verbose_name = _("Service Video")
        verbose_name_plural = _("Service Videos")

class Product(models.Model):
    name = models.CharField(_("Name"), max_length=100)
    description = models.TextField(_("Description"))
    price_per_unit = models.DecimalField(_("Price per unit"), max_digits=10, decimal_places=2)
    unit = models.CharField(_("Unit"), max_length=20, help_text="e.g., square meter, piece")
    category = models.ForeignKey(ServiceCategory, on_delete=models.SET_NULL, null=True, related_name="products")
    is_active = models.BooleanField(_("Is active"), default=True)
    
    class Meta:
        verbose_name = _("Product")
        verbose_name_plural = _("Products")
    
    def __str__(self):
        return self.name


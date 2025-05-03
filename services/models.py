from django.db import models
from django.utils.translation import gettext_lazy as _

class ServiceCategory(models.Model):
    name = models.CharField(_("Name"), max_length=100)
    description = models.TextField(_("Description"), blank=True)

    class Meta:
        db_table = 'categoria_servicio'  # Nombre de la tabla en español
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
    slug = models.SlugField(_("Slug"), max_length=100, unique=True, blank=True)

    def get_featured_image(self):
        """
        Devuelve la imagen destacada para este servicio.
        Prioriza las imágenes marcadas con is_featured=True.
        Si ninguna está marcada, devuelve la primera imagen asociada.
        Devuelve None si el servicio no tiene imágenes.
        """
        # Usamos 'images' porque es el related_name en ServiceImage
        featured = self.images.filter(is_featured=True).first()
        if featured:
            return featured
        else:
            # Si no hay destacada, devuelve la primera imagen que encuentre
            # o None si no hay ninguna imagen asociada.
            return self.images.first()
    class Meta:
        db_table = 'servicio'  # Nombre de la tabla en español
        verbose_name = _("Service")
        verbose_name_plural = _("Services")

    def __str__(self):
        return self.name

from django.core.exceptions import ValidationError

class ServiceImage(models.Model):
    service = models.ForeignKey('Service', on_delete=models.CASCADE, related_name='images', verbose_name='Servicio')
    image = models.ImageField(upload_to='services/', blank=True, null=True, verbose_name='Imagen (archivo)')
    image_url = models.TextField(blank=True, null=True, verbose_name='Código de incorporación <iframe>')
    is_featured = models.BooleanField(default=False, verbose_name='Destacada')
    
    class Meta:
        verbose_name = 'Imagen del servicio'
        verbose_name_plural = 'Imágenes del servicio'
    
    def __str__(self):
        return f"Imagen de {self.service.name}"
    
    def clean(self):
        """
        Valida que se proporcione al menos una imagen (archivo o URL) pero no es necesario ambas.
        """
        if not self.image and not self.image_url:
            raise ValidationError("Debes proporcionar una imagen como archivo o una URL de imagen.")
        
    def get_image_source(self):
        """
        Retorna la fuente de la imagen, priorizando la URL si está disponible.
        """
        if self.image_url:
            return self.image_url
        elif self.image:
            return self.image.url
        return None
    

from django.core.exceptions import ValidationError

class ServiceVideo(models.Model):
    service = models.ForeignKey('Service', on_delete=models.CASCADE, related_name='videos', verbose_name='Servicio')
    title = models.CharField(max_length=200, verbose_name='Título')
    video = models.FileField(upload_to='service_videos/', blank=True, null=True, verbose_name='Video (archivo)')
    video_url = models.TextField(blank=True, null=True, verbose_name='Código de incorporación <iframe>')
    
    class Meta:
        verbose_name = 'Video del servicio'
        verbose_name_plural = 'Videos del servicio'
    
    def __str__(self):
        return self.title
    
    def clean(self):
        """
        Valida que se proporcione al menos un video (archivo o URL) pero no es necesario ambos.
        """
        if not self.video and not self.video_url:
            raise ValidationError("Debes proporcionar un video como archivo o una URL de video.")
        
    def get_video_source(self):
        """
        Retorna la fuente del video, priorizando la URL si está disponible.
        """
        if self.video_url:
            return self.video_url
        elif self.video:
            return self.video.url
        return None

class Product(models.Model):
    name = models.CharField(_("Name"), max_length=100)
    description = models.TextField(_("Description"))
    price_per_unit = models.DecimalField(_("Price per unit"), max_digits=10, decimal_places=2)
    unit = models.CharField(_("Unit"), max_length=20, help_text="e.g., square meter, piece")
    category = models.ForeignKey(ServiceCategory, on_delete=models.SET_NULL, null=True, related_name="products")
    is_active = models.BooleanField(_("Is active"), default=True)

    class Meta:
        db_table = 'producto'  # Nombre de la tabla en español
        verbose_name = _("Product")
        verbose_name_plural = _("Products")

    def __str__(self):
        return self.name

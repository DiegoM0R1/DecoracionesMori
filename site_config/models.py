from django.db import models

# Crea tus modelos aquí.
from django.db import models
from django.core.exceptions import ValidationError

class CarouselImage(models.Model):
    title = models.CharField(max_length=100, verbose_name="Título")
    subtitle = models.CharField(max_length=200, blank=True, verbose_name="Subtítulo")
    image = models.ImageField(upload_to='carousel/', verbose_name="Imagen")
    order = models.PositiveSmallIntegerField(default=0, verbose_name="Orden")
    active = models.BooleanField(default=True, verbose_name="Activo")
    button_text = models.CharField(max_length=50, blank=True, verbose_name="Texto del botón")
    button_url = models.CharField(max_length=200, blank=True, verbose_name="URL del botón")
    
    class Meta:
        verbose_name = "Imagen del carrusel"
        verbose_name_plural = "Imágenes del carrusel"
        ordering = ['order']
    
    def __str__(self):
        return self.title

class SiteImage(models.Model):
    LOCATION_CHOICES = [
        ('home_about', 'Imagen Sección Nosotros (Home)'),
        ('home_services', 'Imagen Sección Servicios (Home)'),
        ('home_testimonial1', 'Testimonio 1'),
        ('home_testimonial2', 'Testimonio 2'),
        ('home_testimonial3', 'Testimonio 3'),
        ('about_banner', 'Banner página Nosotros'),
        ('contact_banner', 'Banner página Contacto'),
        ('services_banner', 'Banner página Servicios'),
        ('about_team1', 'Miembro del equipo 1'),
        ('about_team2', 'Miembro del equipo 2'),
        ('about_team3', 'Miembro del equipo 3'),
    ]
    
    location = models.CharField(max_length=50, choices=LOCATION_CHOICES, unique=True, verbose_name="Ubicación")
    title = models.CharField(max_length=100, blank=True, verbose_name="Título/Nombre")
    description = models.TextField(blank=True, verbose_name="Cargo/Descripción breve")
    bio = models.TextField(blank=True, verbose_name="Biografía detallada")
    linkedin_url = models.URLField(blank=True, verbose_name="URL de LinkedIn")
    instagram_url = models.URLField(blank=True, verbose_name="URL de Instagram")
    image = models.ImageField(upload_to='site_images/', verbose_name="Imagen")
    
    class Meta:
        verbose_name = "Imagen del sitio"
        verbose_name_plural = "Imágenes del sitio"
    
    def __str__(self):
        return dict(self.LOCATION_CHOICES)[self.location]

class SiteSettings(models.Model):
    site_name = models.CharField(max_length=100, default="Decoraciones Mori", verbose_name="Nombre del sitio")
    logo = models.ImageField(upload_to='site_settings/', verbose_name="Logo")
    favicon = models.ImageField(upload_to='site_settings/', blank=True, null=True, verbose_name="Favicon")
    footer_text = models.TextField(blank=True, verbose_name="Texto del pie de página")
    
    # Redes sociales
    facebook_url = models.URLField(blank=True, verbose_name="URL de Facebook")
    instagram_url = models.URLField(blank=True, verbose_name="URL de Instagram")
    whatsapp_number = models.CharField(max_length=20, blank=True, verbose_name="Número de WhatsApp")
    
    # Contacto
    address = models.TextField(blank=True, verbose_name="Dirección")
    phone = models.CharField(max_length=20, blank=True, verbose_name="Teléfono")
    email = models.EmailField(blank=True, verbose_name="Email")
    
    class Meta:
        verbose_name = "Configuración del sitio"
        verbose_name_plural = "Configuración del sitio"
    
    def __str__(self):
        return "Configuración del sitio"
    
    def save(self, *args, **kwargs):
        if SiteSettings.objects.exists() and not self.pk:
            # Si ya existe una configuración y estamos intentando crear otra, lanzamos error
            raise ValidationError("Ya existe una configuración del sitio")
        return super().save(*args, **kwargs)
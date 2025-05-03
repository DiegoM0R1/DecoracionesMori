# services/forms.py
from django import forms
from django.utils.translation import gettext_lazy as _
from .models import Service, ServiceCategory, ServiceImage, ServiceVideo, Product

class ServiceImageForm(forms.ModelForm):
    """
    Formulario personalizado para ServiceImage que mejora la experiencia de usuario
    al aclarar que solo es necesario proporcionar una imagen O una URL, no ambas.
    """
    class Meta:
        model = ServiceImage
        fields = ['service', 'image', 'image_url', 'is_featured']
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['image'].help_text = _("Sube una imagen desde tu dispositivo O proporciona una URL, no es necesario ambas.")
        self.fields['image_url'].help_text = _("URL de una imagen en internet. No es necesario si has subido una imagen.")
    
    def clean(self):
        """
        Valida que se proporcione al menos una imagen (archivo o URL).
        """
        cleaned_data = super().clean()
        image = cleaned_data.get('image')
        image_url = cleaned_data.get('image_url')
        
        if not image and not image_url:
            raise forms.ValidationError(_("Debes proporcionar una imagen como archivo o una URL de imagen."))
        
        return cleaned_data

class ServiceVideoForm(forms.ModelForm):
    """
    Formulario personalizado para ServiceVideo que mejora la experiencia de usuario
    al aclarar que solo es necesario proporcionar un video O una URL, no ambos.
    """
    class Meta:
        model = ServiceVideo
        fields = ['service', 'title', 'video', 'video_url']
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['video'].help_text = _("Sube un video desde tu dispositivo O proporciona una URL, no es necesario ambos.")
        self.fields['video_url'].help_text = _("URL de un video en internet. No es necesario si has subido un video.")
    
    def clean(self):
        """
        Valida que se proporcione al menos un video (archivo o URL).
        """
        cleaned_data = super().clean()
        video = cleaned_data.get('video')
        video_url = cleaned_data.get('video_url')
        
        if not video and not video_url:
            raise forms.ValidationError(_("Debes proporcionar un video como archivo o una URL de video."))
        
        return cleaned_data

class ServiceForm(forms.ModelForm):
    """
    Formulario personalizado para Service con validaciones adicionales
    y mejoras en la experiencia de usuario.
    """
    class Meta:
        model = Service
        fields = ['name', 'slug', 'category', 'description', 'base_price', 'is_active']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 5, 'cols': 80}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['slug'].help_text = _("Identificador único para URL. Se genera automáticamente desde el nombre.")
        self.fields['is_active'].help_text = _("Determina si el servicio está disponible para los clientes.")

class ServiceCategoryForm(forms.ModelForm):
    """
    Formulario personalizado para ServiceCategory.
    """
    class Meta:
        model = ServiceCategory
        fields = ['name', 'description']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3, 'cols': 80}),
        }

class ProductForm(forms.ModelForm):
    """
    Formulario personalizado para Product.
    """
    class Meta:
        model = Product
        fields = ['name', 'category', 'description', 'price_per_unit', 'unit', 'is_active']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 5, 'cols': 80}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['is_active'].help_text = _("Determina si el producto está disponible para los clientes.")
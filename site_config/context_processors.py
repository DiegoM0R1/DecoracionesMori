from .models import SiteSettings, SiteImage, CarouselImage

def site_settings(request):
    try:
        settings = SiteSettings.objects.first()
    except:
        settings = None
    
    try:
        carousel_images = CarouselImage.objects.filter(active=True).order_by('order')
    except:
        carousel_images = []
    
    try:
        site_images = {img.location: img for img in SiteImage.objects.all()}
    except:
        site_images = {}
    
    return {
        'site_settings': settings,
        'carousel_images': carousel_images,
        'site_images': site_images
    }
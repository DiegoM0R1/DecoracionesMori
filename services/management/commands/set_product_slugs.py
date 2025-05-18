from django.core.management.base import BaseCommand
from django.utils.text import slugify
from services.models import Product

class Command(BaseCommand):
    help = 'Asigna slugs únicos a todos los productos'
    
    def handle(self, *args, **options):
        products = Product.objects.all()
        self.stdout.write(f"Actualizando {products.count()} productos...")
        
        for product in products:
            if not product.slug:  # Solo actualiza productos sin slug
                base_slug = slugify(product.name)
                slug = base_slug
                counter = 1
                
                # Verificar si el slug ya existe y crear uno único si es necesario
                while Product.objects.filter(slug=slug).exists():
                    slug = f"{base_slug}-{counter}"
                    counter += 1
                
                product.slug = slug
                product.save(update_fields=['slug'])
                self.stdout.write(f"Actualizado: {product.name} → {slug}")
        
        self.stdout.write(self.style.SUCCESS('¡Todos los productos tienen slugs únicos!'))
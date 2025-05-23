from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from services.models import Product
from .models import InventoryMovement, InventoryStatus

@receiver(post_save, sender=Product)
def create_inventory_status(sender, instance, created, **kwargs):
    """Crea un estado de inventario cuando se crea un nuevo producto"""
    if created:
        InventoryStatus.objects.get_or_create(
            product=instance,
            defaults={'current_stock': instance.stock}
        )

@receiver(post_save, sender=InventoryMovement)
def update_inventory_after_movement(sender, instance, **kwargs):
    """Actualiza el inventario después de un movimiento, si no es borrador"""
    if not instance.draft:
        inventory, created = InventoryStatus.objects.get_or_create(
            product=instance.product,
            defaults={'current_stock': 0}
        )
        inventory.update_stock()

@receiver(post_delete, sender=InventoryMovement)
def update_inventory_after_movement_delete(sender, instance, **kwargs):
    """Actualiza el inventario después de eliminar un movimiento"""
    try:
        inventory = InventoryStatus.objects.get(product=instance.product)
        inventory.update_stock()
    except InventoryStatus.DoesNotExist:
        pass
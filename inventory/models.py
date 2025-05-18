from django.db import models
from django.utils.translation import gettext_lazy as _
# from para productos
from services.models import Product

# Create your models here.
class InventoryMovement(models.Model):
    MOVEMENT_TYPE_CHOICES = (
        ('entrada', _('Entrada')),
        ('salida', _('Salida')),
    )
    
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='movements')
    quantity = models.DecimalField(_('Cantidad'), max_digits=10, decimal_places=2)
    movement_type = models.CharField(_('Tipo de Movimiento'), max_length=10, choices=MOVEMENT_TYPE_CHOICES)
    document_reference = models.CharField(_('Documento de referencia'), max_length=20, blank=True, null=True)
    invoice_item = models.ForeignKey('invoices.InvoiceItem', on_delete=models.SET_NULL, null=True, blank=True)
    notes = models.TextField(_('Notas'), blank=True)
    created_at = models.DateTimeField(_('Fecha de registro'), auto_now_add=True)
    
    class Meta:
        verbose_name = _('Movimiento de Inventario')
        verbose_name_plural = _('Movimientos de Inventario')
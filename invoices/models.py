# invoices/models.py
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.conf import settings
from services.models import Service, Product
from django.utils import timezone
import datetime
from django.core.exceptions import ValidationError
from django.db.models import Sum
from decimal import Decimal
from appointments.models import Appointment

class Invoice(models.Model):
    """
    Modelo principal para boletas de venta
    """
    INVOICE_TYPE_CHOICES = (
        ('boleta', _('Boleta de Venta')),
        ('factura', _('Factura')),
    )
    
    PAYMENT_METHOD_CHOICES = (
        ('efectivo', _('Efectivo')),
        ('tarjeta', _('Tarjeta')),
        ('transferencia', _('Transferencia')),
        ('yape', _('Yape')),
        ('plin', _('Plin')),
        ('otro', _('Otro')),
    )
    
    STATUS_CHOICES = (
        ('borrador', _('Borrador')),
        ('emitida', _('Emitida')),
        ('anulada', _('Anulada')),
        ('pagada', _('Pagada')),
    )
    
    # Información principal
    invoice_type = models.CharField(_('Tipo de Documento'), max_length=10, choices=INVOICE_TYPE_CHOICES, default='boleta')
    series = models.CharField(_('Serie'), max_length=4, default='B001')
    number = models.PositiveIntegerField(_('Número'), blank=True, null=True)
    date_issued = models.DateField(_('Fecha de Emisión'), default=timezone.now)
    
    # Cliente
    client = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='invoices',
        verbose_name=_('Cliente')
    )
    
    # Estado y pagos
    status = models.CharField(_('Estado'), max_length=10, choices=STATUS_CHOICES, default='borrador')
    payment_method = models.CharField(_('Método de Pago'), max_length=15, choices=PAYMENT_METHOD_CHOICES, default='efectivo')
    payment_reference = models.CharField(_('Referencia de Pago'), max_length=50, blank=True, null=True)
    
    # Totales (calculados automáticamente)
    subtotal = models.DecimalField(_('Subtotal'), max_digits=10, decimal_places=2, default=0)
    igv = models.DecimalField(_('IGV (18%)'), max_digits=10, decimal_places=2, default=0)
    total = models.DecimalField(_('Total'), max_digits=10, decimal_places=2, default=0)
    
    # Metadatos
    created_at = models.DateTimeField(_('Fecha de Creación'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Fecha de Actualización'), auto_now=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_invoices',
        verbose_name=_('Creado por')
    )
    notes = models.TextField(_('Observaciones'), blank=True)

    appointment = models.ForeignKey(
        Appointment,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='invoices',
        verbose_name=_('Cita relacionada')
    )
    
    # Nuevos campos para manejo de pagos parciales
    advance_payment = models.DecimalField(
        _('Adelanto recibido'), 
        max_digits=10, 
        decimal_places=2, 
        default=0
    )
    pending_balance = models.DecimalField(
        _('Saldo pendiente'), 
        max_digits=10, 
        decimal_places=2, 
        default=0
    )
    
    # Campo para controlar si ya se afectó el inventario
    inventory_processed = models.BooleanField(
        _('Inventario procesado'), 
        default=False,
        help_text=_('Indica si los productos de esta boleta ya afectaron el inventario')
    )
    
    class Meta:
        db_table = 'boleta_venta'
        verbose_name = _('Boleta de Venta')
        verbose_name_plural = _('Facturación')
        ordering = ['-date_issued', '-number']
        # Restricción única para serie y número
        unique_together = ['series', 'number']
    
    def __str__(self):
        return f"{self.series}-{self.number or '(borrador)'} - {self.client.get_full_name() or self.client.username}"
    
    def save(self, *args, **kwargs):
        # Detectar si el estado cambió a 'pagada'
        old_status = None
        if self.pk:
            try:
                old_status = Invoice.objects.get(pk=self.pk).status
            except Invoice.DoesNotExist:
                old_status = None
        
        # Asignar automáticamente el siguiente número en la serie si está en borrador y se cambia a emitida
        if self.status == 'emitida' and not self.number:
            last_invoice = Invoice.objects.filter(series=self.series).order_by('-number').first()
            self.number = 1 if not last_invoice or not last_invoice.number else last_invoice.number + 1
        
        # Calcular totales SOLO si la instancia ya tiene un ID
        if self.pk is not None and self.invoiceitem_set.exists():
            self.subtotal = self.invoiceitem_set.aggregate(Sum('subtotal'))['subtotal__sum'] or Decimal('0.00')
            self.igv = self.subtotal * Decimal('0.18')
            self.total = self.subtotal + self.igv
        
        self.pending_balance = self.total - self.advance_payment
        
        # Si es una boleta asociada a una cita y hay un adelanto de al menos 50 soles,
        # cambiar el estado de la cita a confirmada
        if self.appointment and self.appointment.status == 'pending' and self.advance_payment >= 50:
            self.appointment.status = 'confirmed'
            self.appointment.save(update_fields=['status'])
        
        super().save(*args, **kwargs)
        
        # NUEVO: Procesar inventario solo cuando se marca como pagada
        if (old_status != 'pagada' and self.status == 'pagada' and not self.inventory_processed):
            self.process_inventory()
    
    def process_inventory(self):
        """Procesa el inventario cuando la boleta se marca como pagada"""
        from inventory.models import InventoryMovement
        
        # Procesar cada item de producto en la boleta
        for item in self.invoiceitem_set.filter(item_type='product', product__isnull=False):
            # Crear movimiento de salida de inventario
            InventoryMovement.objects.create(
                product=item.product,
                quantity=item.quantity,
                movement_type='salida',
                document_reference=f"{self.series}-{self.number or '(borrador)'}",
                invoice_item=item,
                notes=f"Venta de producto en {self.invoice_type} - Boleta pagada",
                draft=False  # Movimiento confirmado
            )
        
        # Marcar como procesado para evitar duplicados
        self.inventory_processed = True
        self.save(update_fields=['inventory_processed'])


class InvoiceItem(models.Model):
    """
    Detalle de elementos en la boleta
    """
    ITEM_TYPE_CHOICES = (
        ('service', _('Servicio')),
        ('product', _('Producto')),
        ('other', _('Otro')),
    )
    
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, verbose_name=_('Boleta'))
    item_type = models.CharField(_('Tipo de Ítem'), max_length=10, choices=ITEM_TYPE_CHOICES)
    
    # Referencia a producto o servicio (opcional)
    service = models.ForeignKey(Service, on_delete=models.SET_NULL, null=True, blank=True, verbose_name=_('Servicio'))
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True, blank=True, verbose_name=_('Producto'))
    
    # Descripción manual (se usa cuando no hay referencia a producto/servicio)
    description = models.CharField(_('Descripción'), max_length=255)
    
    # Cantidades y precios
    quantity = models.DecimalField(_('Cantidad'), max_digits=10, decimal_places=2, default=1)
    unit_price = models.DecimalField(_('Precio Unitario'), max_digits=10, decimal_places=2)
    discount = models.DecimalField(_('Descuento'), max_digits=10, decimal_places=2, default=0)
    subtotal = models.DecimalField(_('Subtotal'), max_digits=10, decimal_places=2)

    appointment = models.ForeignKey(
        Appointment,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='related_invoice_items',
        verbose_name=_('Cita relacionada')
    )
    
    # Nuevos campos para manejo de pagos parciales
    advance_payment = models.DecimalField(
        _('Adelanto recibido'), 
        max_digits=10, 
        decimal_places=2, 
        default=0
    )
    pending_balance = models.DecimalField(
        _('Saldo pendiente'), 
        max_digits=10, 
        decimal_places=2, 
        default=0
    )
    
    class Meta:
        db_table = 'detalle_boleta'
        verbose_name = _('Detalle de Boleta')
        verbose_name_plural = _('Detalles de Boleta')
    
    def __str__(self):
        return f"{self.quantity} x {self.description} - {self.subtotal}"
    
    def clean(self):
        """Validaciones personalizadas"""
        super().clean()
        
        # Verificar que se seleccione un producto o servicio según el tipo de ítem
        if self.item_type == 'service' and not self.service:
            raise ValidationError({'service': _('Debe seleccionar un servicio.')})
        if self.item_type == 'product' and not self.product:
            raise ValidationError({'product': _('Debe seleccionar un producto.')})
        
        # Autocompletar precio unitario si no está establecido o es cero
        if not self.unit_price or self.unit_price == 0:
            if self.item_type == 'product' and self.product:
                self.unit_price = self.product.price_per_unit
            elif self.item_type == 'service' and self.service:
                self.unit_price = self.service.base_price
        
        # Si no hay descripción manual, tomar del producto/servicio
        if not self.description:
            if self.service:
                self.description = self.service.name
            elif self.product:
                self.description = self.product.name
        
        # Asegurar valores para cálculos
        if self.unit_price is None:
            self.unit_price = Decimal('0.00')
        if self.quantity is None:
            self.quantity = Decimal('1.00')
        if self.discount is None:
            self.discount = Decimal('0.00')
        
        # Auto-calcular el subtotal
        self.subtotal = (self.unit_price * self.quantity) - self.discount
    
    def save(self, *args, **kwargs):
        if (self.unit_price is None or self.unit_price == 0) and self.product:
            self.unit_price = self.product.price_per_unit
        elif (self.unit_price is None or self.unit_price == 0) and self.service:
            self.unit_price = self.service.base_price
        
        # Calcular subtotal primero
        self.subtotal = (self.unit_price * self.quantity) - self.discount
        self.pending_balance = self.subtotal - self.advance_payment
        
        # Asegurar que los cálculos están actualizados
        if not self.pending_balance or self.pending_balance == 0:
            self.pending_balance = self.subtotal - self.advance_payment
        
        if not self.description:
            if self.service:
                self.description = self.service.name
            elif self.product:
                self.description = self.product.name
            else:
                self.description = 'Item sin descripción'
        
        if self.appointment and self.appointment.status == 'pending' and self.advance_payment >= 50:
            self.appointment.status = 'confirmed'
            self.appointment.save(update_fields=['status'])
        
        # Guardar el item actual primero
        super().save(*args, **kwargs)
        
        # Si es un servicio, agregar los productos relacionados automáticamente
        if self.item_type == 'service' and self.service:
            from services.models import ServiceComponent
            
            # Buscar todos los componentes (productos) asociados a este servicio
            components = ServiceComponent.objects.filter(service=self.service)
            
            # Para cada componente, crear un nuevo InvoiceItem de tipo producto
            for component in components:
                # Verificar si ya existe un ítem para este componente en la misma factura
                product_item_exists = InvoiceItem.objects.filter(
                    invoice=self.invoice,
                    item_type='product',
                    product=component.product,
                    description__contains=f"Usado en {self.service.name}"
                ).exists()
                
                # Si no existe, crearlo
                if not product_item_exists:
                    InvoiceItem.objects.create(
                        invoice=self.invoice,
                        item_type='product',
                        product=component.product,
                        description=f"{component.product.name} - Usado en {self.service.name}",
                        quantity=component.quantity * self.quantity,
                        unit_price=component.product.price_per_unit,
                        subtotal=component.product.price_per_unit * component.quantity * self.quantity,
                        appointment=self.appointment
                    )
        
        # REMOVIDO: Ya no creamos movimientos de inventario aquí
        # El inventario se procesa solo cuando la boleta se marca como pagada
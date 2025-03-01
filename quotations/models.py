# quotations/models.py
from django.db import models
from django.utils.translation import gettext_lazy as _
from accounts.models import User
from services.models import Service, Product
from appointments.models import Appointment

class Quotation(models.Model):
    STATUS_CHOICES = (
        ("draft", _("Draft")),
        ("sent", _("Sent")),
        ("accepted", _("Accepted")),
        ("rejected", _("Rejected")),
    )
    
    client = models.ForeignKey(User, on_delete=models.CASCADE, related_name="quotations")
    appointment = models.OneToOneField(Appointment, on_delete=models.SET_NULL, null=True, blank=True)
    staff = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name="created_quotations", limit_choices_to={"is_staff": True})
    
    quotation_number = models.CharField(_("Quotation Number"), max_length=20, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    valid_until = models.DateField(_("Valid Until"))
    
    status = models.CharField(_("Status"), max_length=20, choices=STATUS_CHOICES, default="draft")
    total_amount = models.DecimalField(_("Total Amount"), max_digits=10, decimal_places=2)
    
    notes = models.TextField(_("Notes"), blank=True)
    
    class Meta:
        verbose_name = _("Quotation")
        verbose_name_plural = _("Quotations")
    
    def __str__(self):
        return f"Quotation #{self.quotation_number} for {self.client.username}"
    
    def save(self, *args, **kwargs):
        if not self.quotation_number:
            # Generate a quotation number (you'd implement this logic)
            last_quotation = Quotation.objects.order_by('-id').first()
            if last_quotation:
                last_id = last_quotation.id
            else:
                last_id = 0
            self.quotation_number = f"QT-{last_id + 1:06d}"
        super().save(*args, **kwargs)

class QuotationItem(models.Model):
    ITEM_TYPE_CHOICES = (
        ("service", _("Service")),
        ("product", _("Product")),
    )
    
    quotation = models.ForeignKey(Quotation, on_delete=models.CASCADE, related_name="items")
    item_type = models.CharField(_("Item Type"), max_length=10, choices=ITEM_TYPE_CHOICES)
    
    service = models.ForeignKey(Service, on_delete=models.SET_NULL, null=True, blank=True)
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True, blank=True)
    
    description = models.CharField(_("Description"), max_length=200)
    quantity = models.DecimalField(_("Quantity"), max_digits=10, decimal_places=2)
    unit_price = models.DecimalField(_("Unit Price"), max_digits=10, decimal_places=2)
    total_price = models.DecimalField(_("Total Price"), max_digits=10, decimal_places=2)
    
    class Meta:
        verbose_name = _("Quotation Item")
        verbose_name_plural = _("Quotation Items")
    
    def __str__(self):
        return f"{self.description} - {self.quantity} x {self.unit_price}"
    
    def save(self, *args, **kwargs):
        self.total_price = self.quantity * self.unit_price
        super().save(*args, **kwargs)
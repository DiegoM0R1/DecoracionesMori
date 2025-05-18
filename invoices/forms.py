# invoices/forms.py
from django import forms
from .models import InvoiceItem

class InvoiceItemForm(forms.ModelForm):
    class Meta:
        model = InvoiceItem
        fields = ['item_type', 'service', 'product', 'description', 'quantity', 
                 'unit_price', 'discount', 'subtotal', 'advance_payment', 'pending_balance']
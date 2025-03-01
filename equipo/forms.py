from django import forms
from django.utils.translation import gettext_lazy as _
from .models import Appointment, StaffAvailability
from servicios.models import Service
from cuentas.models import User

class AppointmentRequestForm(forms.ModelForm):
    name = forms.CharField(max_length=100)
    dni = forms.CharField(max_length=20)
    email = forms.EmailField()
    phone_number = forms.CharField(max_length=15)
    address = forms.CharField(widget=forms.Textarea)
    preferred_date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}))
    preferred_time = forms.ChoiceField(choices=[], required=False)
    
    class Meta:
        model = Appointment
        fields = ['service', 'notes']
        widgets = {
            'service': forms.HiddenInput(),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # You'd dynamically populate this with available times
        self.fields['preferred_time'].choices = [
            ('', _('Select a time')),
            ('morning', _('Morning (9:00 - 12:00)')),
            ('afternoon', _('Afternoon (13:00 - 17:00)')),
        ]
        
        # If there's an initial service, hide the service field
        if 'service' in self.initial:
            self.fields['service'].widget = forms.HiddenInput()
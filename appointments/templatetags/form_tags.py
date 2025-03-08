from django import template
from django.forms.boundfield import BoundField

register = template.Library()

@register.filter(name='add_class')
def add_class(value, arg):
    """
    Adds a CSS class to a form field
    """
    if isinstance(value, BoundField):
        # Si el valor es un campo de formulario
        existing_classes = value.field.widget.attrs.get('class', '')
        new_classes = f"{existing_classes} {arg}".strip()
        value.field.widget.attrs['class'] = new_classes
        return value
    return value
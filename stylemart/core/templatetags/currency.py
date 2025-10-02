from django import template

register = template.Library()

@register.filter
def pkr(value):
    try:
        return f"PKR {float(value):,.2f}"
    except (ValueError, TypeError):
        return "PKR 0.00"

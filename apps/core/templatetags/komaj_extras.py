from decimal import Decimal

from django import template
from django.utils.safestring import mark_safe

register = template.Library()

_EN_TO_FA = str.maketrans("0123456789", "۰۱۲۳۴۵۶۷۸۹")


@register.filter(name="fa", is_safe=True)
def to_persian_digits(value):
    if value is None:
        return ""
    return str(value).translate(_EN_TO_FA)


@register.filter(name="toman", is_safe=True)
def format_toman(value):
    if value is None or value == "":
        return ""
    try:
        amount = Decimal(value)
    except (ValueError, TypeError):
        return str(value)
    whole = int(amount)
    grouped = f"{whole:,}".replace(",", "٬")
    return mark_safe(grouped.translate(_EN_TO_FA))


@register.filter(name="kg")
def format_kg(value):
    if value is None:
        return ""
    try:
        amount = Decimal(value)
    except (ValueError, TypeError):
        return str(value)
    if amount == amount.to_integral_value():
        text = f"{int(amount)}"
    else:
        text = f"{amount.normalize():f}".rstrip("0").rstrip(".")
    return text.replace(".", "٫").translate(_EN_TO_FA)

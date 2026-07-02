import json
from decimal import Decimal

from django import template
from django.utils.safestring import mark_safe

register = template.Library()

_EN_TO_FA = str.maketrans("0123456789", "۰۱۲۳۴۵۶۷۸۹")


@register.simple_tag(name="ld_json")
def ld_json(data):
    """Render a dict as a <script type="application/ld+json"> block.

    JSON is embedded XSS-safely: <, > and & are unicode-escaped so admin-authored
    product text can't break out of the script (OWASP JSON-in-HTML rule).
    """
    payload = json.dumps(data, ensure_ascii=False)
    payload = payload.replace("<", "\\u003c").replace(">", "\\u003e").replace("&", "\\u0026")
    return mark_safe(f'<script type="application/ld+json">{payload}</script>')


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

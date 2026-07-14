from django import template
from django.conf import settings

register = template.Library()


@register.inclusion_tag("payments/zibal_trust.html")
def zibal_trust_badge():
    """Zibal's "trusted payment" badge (نشان اعتماد زیبال).

    Renders nothing until ZIBAL_TRUST_SITE names the domain registered with
    Zibal — the badge asserts that payments really are processed by Zibal, so it
    must not appear before the gateway exists.

    Uses Zibal's documented plain-HTML form rather than their <script> tag: the
    script only injects this same anchor, and skipping it keeps a third-party
    script off every page.
    """
    return {"site": getattr(settings, "ZIBAL_TRUST_SITE", "")}

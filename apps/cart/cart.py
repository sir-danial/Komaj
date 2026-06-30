"""Session-backed shopping cart.

Stored in ``request.session[CART_SESSION_KEY]`` as::

    { "<variant_id>": {"quantity": "1.5", "unit_price": "180000"} }

Quantities and prices are kept as strings in the session (JSON-safe) and exposed
as ``Decimal`` through the iterator. ``unit_price`` is a snapshot taken when the
item was added/updated (per research-report: lock the price the customer saw);
checkout re-validates against the live price/stock before payment.
"""
from decimal import Decimal

from apps.catalog.models import ProductVariant

from .totals import compute_totals

CART_SESSION_KEY = "cart"


class Cart:
    def __init__(self, request):
        self.session = request.session
        cart = self.session.get(CART_SESSION_KEY)
        if cart is None:
            cart = self.session[CART_SESSION_KEY] = {}
        self.cart = cart

    # --- mutation -------------------------------------------------------
    def add(self, variant, quantity, *, replace=False):
        """Add ``quantity`` of ``variant``. Validates against min/step/stock.

        ``replace=True`` sets the absolute quantity (used by the cart page);
        otherwise the quantity is added to whatever is already there.
        """
        key = str(variant.pk)
        current = Decimal(self.cart[key]["quantity"]) if key in self.cart else Decimal("0")
        new_qty = quantity if replace else current + Decimal(str(quantity))
        # raises ValidationError if invalid
        new_qty = variant.validate_quantity(new_qty)
        self.cart[key] = {"quantity": str(new_qty), "unit_price": str(variant.unit_price)}
        self.save()

    def remove(self, variant_id):
        key = str(variant_id)
        if key in self.cart:
            del self.cart[key]
            self.save()

    def clear(self):
        self.session[CART_SESSION_KEY] = {}
        self.cart = self.session[CART_SESSION_KEY]
        self.save()

    def save(self):
        self.session.modified = True

    # --- reading --------------------------------------------------------
    def _variants(self):
        ids = [int(k) for k in self.cart.keys()]
        return {v.pk: v for v in ProductVariant.objects.filter(pk__in=ids).select_related("product")}

    def __iter__(self):
        variants = self._variants()
        for key, item in self.cart.items():
            variant = variants.get(int(key))
            if variant is None:
                continue  # variant was deleted — skip (cleaned on next write)
            quantity = Decimal(item["quantity"])
            unit_price = Decimal(item["unit_price"])
            yield {
                "variant": variant,
                "quantity": quantity,
                "unit_price": unit_price,
                "line_total": (unit_price * quantity).quantize(Decimal("1")),
            }

    def __len__(self):
        """Number of distinct line items (the «۳ کالا» badge)."""
        return len(self.cart)

    @property
    def count(self):
        return len(self.cart)

    @property
    def is_empty(self):
        return not self.cart

    @property
    def subtotal(self):
        return sum((item["line_total"] for item in self), Decimal("0"))

    def totals(self, shipping=None, discount=Decimal("0")):
        return compute_totals(self.subtotal, shipping=shipping, discount=discount)

"""Session-backed shopping cart.

The cart is stored in the user's session as a dict keyed by variant ID:

    {
        "12": {"qty": 2, "price": "260.00"},
        "17": {"qty": 1, "price": "85.00"},
    }
"""
from decimal import Decimal

from django.conf import settings

from catalog.models import ProductVariant


class Cart:
    def __init__(self, request):
        self.session = request.session
        cart = self.session.get(settings.CART_SESSION_ID)
        if not cart:
            cart = self.session[settings.CART_SESSION_ID] = {}
        self.cart = cart

    # --- Mutations ---------------------------------------------------------

    def add(self, variant: ProductVariant, quantity: int = 1, replace: bool = False):
        key = str(variant.id)
        if key not in self.cart:
            self.cart[key] = {"qty": 0, "price": str(variant.price)}
        if replace:
            self.cart[key]["qty"] = max(1, quantity)
        else:
            self.cart[key]["qty"] += quantity
        # Always refresh price snapshot so display stays consistent.
        self.cart[key]["price"] = str(variant.price)
        # Cap at variant inventory to avoid overselling.
        self.cart[key]["qty"] = min(self.cart[key]["qty"], max(1, variant.inventory))
        self.save()

    def remove(self, variant_id):
        key = str(variant_id)
        if key in self.cart:
            del self.cart[key]
            self.save()

    def update_quantity(self, variant_id, quantity: int):
        key = str(variant_id)
        if key not in self.cart:
            return
        if quantity <= 0:
            del self.cart[key]
        else:
            self.cart[key]["qty"] = quantity
        self.save()

    def clear(self):
        self.session[settings.CART_SESSION_ID] = {}
        self.cart = self.session[settings.CART_SESSION_ID]
        self.save()

    def save(self):
        self.session.modified = True

    # --- Reads -------------------------------------------------------------

    def __iter__(self):
        variant_ids = [int(k) for k in self.cart.keys()]
        variants = ProductVariant.objects.filter(id__in=variant_ids).select_related(
            "product", "product__category"
        )
        variant_map = {v.id: v for v in variants}
        for key, item in self.cart.items():
            variant = variant_map.get(int(key))
            if not variant:
                continue
            qty = item["qty"]
            price = Decimal(item["price"])
            yield {
                "variant": variant,
                "product": variant.product,
                "qty": qty,
                "price": price,
                "line_total": price * qty,
            }

    def __len__(self):
        return sum(item["qty"] for item in self.cart.values())

    @property
    def subtotal(self) -> Decimal:
        return sum(
            (Decimal(item["price"]) * item["qty"] for item in self.cart.values()),
            Decimal("0.00"),
        )

    @property
    def is_empty(self) -> bool:
        return len(self.cart) == 0

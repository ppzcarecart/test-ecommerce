"""Cart abstraction that combines a session bag (anonymous users) with a
persistent ``SavedCart`` (logged-in users). The two stay in sync — every write
through ``Cart`` updates both sides for an authenticated request, so a guest
cart isn't lost when the user signs in (the merge is performed by
``cart.middleware.CartMergeMiddleware``).
"""
from __future__ import annotations

from decimal import Decimal

from django.conf import settings

from catalog.models import ProductVariant


class Cart:
    def __init__(self, request):
        self.request = request
        self.session = request.session
        cart = self.session.get(settings.CART_SESSION_ID)
        if not cart:
            cart = self.session[settings.CART_SESSION_ID] = {}
        self.cart = cart
        self.user = (
            getattr(request, "user", None)
            if getattr(getattr(request, "user", None), "is_authenticated", False)
            else None
        )

    # --- Mutations ---------------------------------------------------------

    def add(self, variant: ProductVariant, quantity: int = 1, replace: bool = False):
        key = str(variant.id)
        if key not in self.cart:
            self.cart[key] = {"qty": 0, "price": str(variant.price)}
        if replace:
            self.cart[key]["qty"] = max(1, quantity)
        else:
            self.cart[key]["qty"] += quantity
        self.cart[key]["price"] = str(variant.price)
        # Cap at variant inventory to avoid overselling.
        self.cart[key]["qty"] = min(
            self.cart[key]["qty"], max(1, variant.inventory)
        )
        self._persist_item(variant, self.cart[key]["qty"], variant.price)
        self.save()

    def remove(self, variant_id):
        key = str(variant_id)
        if key in self.cart:
            del self.cart[key]
            self._persist_remove(variant_id)
            self.save()

    def update_quantity(self, variant_id, quantity: int):
        key = str(variant_id)
        if key not in self.cart:
            return
        if quantity <= 0:
            del self.cart[key]
            self._persist_remove(variant_id)
        else:
            self.cart[key]["qty"] = quantity
            try:
                variant = ProductVariant.objects.get(pk=int(variant_id))
                self._persist_item(
                    variant, quantity, Decimal(self.cart[key]["price"])
                )
            except ProductVariant.DoesNotExist:
                pass
        self.save()

    def clear(self):
        self.session[settings.CART_SESSION_ID] = {}
        self.cart = self.session[settings.CART_SESSION_ID]
        if self.user:
            from .models import SavedCart

            SavedCart.objects.filter(user=self.user).delete()
        self.save()

    def save(self):
        self.session.modified = True

    # --- Persistence helpers ---------------------------------------------

    def _saved_cart(self):
        if not self.user:
            return None
        from .models import SavedCart

        cart, _ = SavedCart.objects.get_or_create(user=self.user)
        return cart

    def _persist_item(self, variant: ProductVariant, qty: int, price: Decimal):
        cart = self._saved_cart()
        if cart is None:
            return
        from .models import SavedCartItem

        SavedCartItem.objects.update_or_create(
            cart=cart,
            variant=variant,
            defaults={"quantity": qty, "price": price},
        )

    def _persist_remove(self, variant_id):
        cart = self._saved_cart()
        if cart is None:
            return
        cart.items.filter(variant_id=variant_id).delete()

    def merge_on_login(self, user):
        """Called from middleware right after login: pull the user's saved
        cart into the session, then re-persist any session-only additions."""
        from .models import SavedCart

        cart, _ = SavedCart.objects.get_or_create(user=user)
        # Pull saved items into the session (additive merge — qty preferred).
        for item in cart.items.select_related("variant").all():
            key = str(item.variant_id)
            if key in self.cart:
                self.cart[key]["qty"] = max(
                    int(self.cart[key]["qty"]), int(item.quantity)
                )
            else:
                self.cart[key] = {
                    "qty": item.quantity,
                    "price": str(item.price),
                }
        # Re-persist the merged session into the saved cart.
        from .models import SavedCartItem

        for key, data in self.cart.items():
            try:
                variant = ProductVariant.objects.get(pk=int(key))
            except ProductVariant.DoesNotExist:
                continue
            SavedCartItem.objects.update_or_create(
                cart=cart,
                variant=variant,
                defaults={
                    "quantity": int(data["qty"]),
                    "price": Decimal(str(data["price"])),
                },
            )
        self.save()

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

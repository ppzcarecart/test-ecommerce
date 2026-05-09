"""Database-backed cart persistence for logged-in users."""
from __future__ import annotations

from decimal import Decimal

from django.conf import settings
from django.db import models


class SavedCart(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        related_name="saved_cart",
        on_delete=models.CASCADE,
    )
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return f"Cart for {self.user}"


class SavedCartItem(models.Model):
    cart = models.ForeignKey(
        SavedCart, related_name="items", on_delete=models.CASCADE
    )
    variant = models.ForeignKey(
        "catalog.ProductVariant",
        related_name="saved_cart_items",
        on_delete=models.CASCADE,
    )
    quantity = models.PositiveIntegerField(default=1)
    price = models.DecimalField(
        max_digits=10, decimal_places=2, default=Decimal("0")
    )

    class Meta:
        unique_together = ("cart", "variant")

    def __str__(self) -> str:
        return f"{self.variant} × {self.quantity}"

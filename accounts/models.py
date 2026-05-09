"""User-side models: shipping addresses + wishlist."""
from __future__ import annotations

from django.conf import settings
from django.db import models


class Address(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="addresses",
        on_delete=models.CASCADE,
    )
    full_name = models.CharField(max_length=200)
    address_line1 = models.CharField(max_length=255)
    address_line2 = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=120)
    postal_code = models.CharField(max_length=32)
    country = models.CharField(max_length=64, default="US")
    is_default = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-is_default", "-created_at")

    def __str__(self) -> str:
        return f"{self.full_name} — {self.city}, {self.country}"


class WishlistItem(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="wishlist",
        on_delete=models.CASCADE,
    )
    product = models.ForeignKey(
        "catalog.Product", related_name="wishlisted_by", on_delete=models.CASCADE
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "product")
        ordering = ("-created_at",)

    def __str__(self) -> str:
        return f"{self.user} ♥ {self.product}"

from decimal import Decimal

from django.conf import settings
from django.db import models


class Order(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        PAID = "paid", "Paid"
        FAILED = "failed", "Failed"
        CANCELLED = "cancelled", "Cancelled"
        REFUNDED = "refunded", "Refunded"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="orders",
        null=True,
        blank=True,
    )

    email = models.EmailField()
    full_name = models.CharField(max_length=200)
    address_line1 = models.CharField(max_length=255)
    address_line2 = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=120)
    postal_code = models.CharField(max_length=32)
    country = models.CharField(max_length=64, default="US")

    subtotal = models.DecimalField(
        max_digits=12, decimal_places=2, default=Decimal("0")
    )
    shipping = models.DecimalField(
        max_digits=12, decimal_places=2, default=Decimal("0")
    )
    tax = models.DecimalField(
        max_digits=12, decimal_places=2, default=Decimal("0")
    )
    total = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0"))
    currency = models.CharField(max_length=8, default="USD")

    stripe_payment_intent_id = models.CharField(
        max_length=255, blank=True, db_index=True
    )
    stripe_client_secret = models.CharField(max_length=255, blank=True)
    status = models.CharField(
        max_length=16, choices=Status.choices, default=Status.PENDING
    )

    confirmation_email_sent_at = models.DateTimeField(null=True, blank=True)
    inventory_decremented_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-created_at",)

    def __str__(self) -> str:
        return f"Order #{self.pk} — {self.email} ({self.status})"


class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name="items", on_delete=models.CASCADE)
    variant = models.ForeignKey(
        "catalog.ProductVariant", on_delete=models.PROTECT, related_name="order_items"
    )
    product_name = models.CharField(max_length=200)
    variant_name = models.CharField(max_length=200)
    sku = models.CharField(max_length=64)
    unit_price = models.DecimalField(max_digits=12, decimal_places=2)
    quantity = models.PositiveIntegerField()

    @property
    def line_total(self) -> Decimal:
        return self.unit_price * self.quantity

    def __str__(self) -> str:
        return f"{self.product_name} — {self.variant_name} × {self.quantity}"


class StripeEvent(models.Model):
    """Idempotency log for Stripe webhook events.

    Webhook handlers MUST short-circuit if the event id is already present
    here — Stripe retries successful events on transient network errors,
    so naive handling double-charges or double-decrements inventory.
    """

    event_id = models.CharField(max_length=255, unique=True)
    event_type = models.CharField(max_length=120, db_index=True)
    payload = models.JSONField(default=dict)
    received_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(null=True, blank=True)
    error = models.TextField(blank=True)

    def __str__(self) -> str:
        return f"{self.event_type} ({self.event_id})"

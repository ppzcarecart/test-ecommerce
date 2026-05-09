"""Checkout flow + Stripe webhook idempotency."""
from __future__ import annotations

import json

import pytest
from django.urls import reverse

from payments.models import Order, StripeEvent


@pytest.mark.django_db
def test_checkout_creates_order(client, variant):
    client.post(reverse("cart:add", args=[variant.id]), {"qty": 2})
    res = client.post(
        reverse("payments:checkout"),
        {
            "email": "buyer@example.com",
            "full_name": "Test Buyer",
            "address_line1": "1 Bond St",
            "address_line2": "",
            "city": "London",
            "postal_code": "W1S 4QQ",
            "country": "GB",
        },
    )
    assert res.status_code in (302, 303)
    order = Order.objects.order_by("-id").first()
    assert order is not None
    assert order.email == "buyer@example.com"
    assert order.items.count() == 1
    assert order.items.first().quantity == 2
    # Subtotal = 2 * 100 = 200; GB shipping = 30; tax = 20%*230 = 46
    assert order.subtotal == 200
    assert order.shipping == 30
    assert order.tax == 46
    assert order.total == 276


@pytest.mark.django_db
def test_webhook_payment_succeeded_marks_paid_and_decrements_inventory(client, variant):
    # Build an order tied to a fake intent.
    order = Order.objects.create(
        email="buyer@example.com",
        full_name="Buyer",
        address_line1="1 Test St",
        city="NYC",
        postal_code="10001",
        country="US",
        subtotal=200,
        shipping=12,
        tax=15,
        total=227,
        currency="USD",
        stripe_payment_intent_id="pi_test_123",
        status=Order.Status.PENDING,
    )
    from payments.models import OrderItem

    OrderItem.objects.create(
        order=order,
        variant=variant,
        product_name=variant.product.name,
        variant_name=variant.name,
        sku=variant.sku,
        unit_price=variant.price,
        quantity=2,
    )

    payload = {
        "id": "evt_test_001",
        "type": "payment_intent.succeeded",
        "data": {"object": {"id": "pi_test_123"}},
    }
    body = json.dumps(payload).encode()
    res = client.post(
        reverse("payments:webhook"),
        data=body,
        content_type="application/json",
    )
    assert res.status_code == 200, res.content

    order.refresh_from_db()
    variant.refresh_from_db()
    assert order.status == Order.Status.PAID
    assert variant.inventory == 10 - 2  # decremented
    assert StripeEvent.objects.filter(event_id="evt_test_001").exists()

    # Replay the same event — should be a no-op (idempotent)
    res2 = client.post(
        reverse("payments:webhook"),
        data=body,
        content_type="application/json",
    )
    assert res2.status_code == 200
    variant.refresh_from_db()
    assert variant.inventory == 10 - 2  # NOT decremented twice

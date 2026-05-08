"""Thin wrapper around Stripe payment intents.

The default settings ship with placeholder keys (``sk_test_stub`` etc.) so we
intentionally avoid hitting Stripe's API until real keys are configured. The
``create_payment_intent`` helper detects stub keys and returns a fake intent
that mimics the shape of ``stripe.PaymentIntent`` so the checkout flow stays
exercisable in development without network calls.
"""
from __future__ import annotations

import secrets
from dataclasses import dataclass
from decimal import Decimal
from typing import Optional

from django.conf import settings


@dataclass
class StubPaymentIntent:
    id: str
    client_secret: str
    amount: int
    currency: str
    status: str = "requires_payment_method"


def _is_stub_key(key: str) -> bool:
    return (not key) or key.endswith("stub") or key.endswith("replace_me")


def to_stripe_amount(amount: Decimal, currency: str) -> int:
    """Convert a Decimal price into the smallest Stripe currency unit (cents)."""
    zero_decimal = {"BIF", "JPY", "KRW", "VND", "XAF", "XOF"}
    if currency.upper() in zero_decimal:
        return int(amount.quantize(Decimal("1")))
    return int((amount * 100).quantize(Decimal("1")))


def create_payment_intent(
    amount: Decimal,
    currency: str,
    metadata: Optional[dict] = None,
) -> StubPaymentIntent:
    """Create a Stripe PaymentIntent (or a stub if no live key is configured)."""
    stripe_amount = to_stripe_amount(amount, currency)

    if _is_stub_key(settings.STRIPE_SECRET_KEY):
        # Local / CI mode — mint a fake intent so the UI flow keeps working.
        token = secrets.token_hex(12)
        return StubPaymentIntent(
            id=f"pi_stub_{token}",
            client_secret=f"pi_stub_{token}_secret_{secrets.token_hex(8)}",
            amount=stripe_amount,
            currency=currency.lower(),
        )

    import stripe  # imported lazily so dev installs without the SDK still boot

    stripe.api_key = settings.STRIPE_SECRET_KEY
    intent = stripe.PaymentIntent.create(
        amount=stripe_amount,
        currency=currency.lower(),
        automatic_payment_methods={"enabled": True},
        metadata=metadata or {},
    )
    return StubPaymentIntent(
        id=intent.id,
        client_secret=intent.client_secret,
        amount=intent.amount,
        currency=intent.currency,
        status=intent.status,
    )

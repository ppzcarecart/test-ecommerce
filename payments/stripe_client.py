"""Stripe wrapper.

In dev (any key ending in ``_stub`` / ``_replace_me``), we mint a fake intent
so the checkout flow stays exercisable without network calls. With real keys,
we hit the live Stripe API.
"""
from __future__ import annotations

import logging
import secrets
from dataclasses import dataclass
from decimal import Decimal
from typing import Optional

from django.conf import settings

logger = logging.getLogger(__name__)


@dataclass
class StubPaymentIntent:
    id: str
    client_secret: str
    amount: int
    currency: str
    status: str = "requires_payment_method"


def is_stub_key(key: str) -> bool:
    return (not key) or key.endswith("stub") or key.endswith("replace_me")


def to_stripe_amount(amount: Decimal, currency: str) -> int:
    """Convert a Decimal price into the smallest Stripe currency unit (cents)."""
    zero_decimal = {"BIF", "JPY", "KRW", "VND", "XAF", "XOF"}
    if currency.upper() in zero_decimal:
        return int(amount.quantize(Decimal("1")))
    return int((amount * 100).quantize(Decimal("1")))


def _stripe_client():
    import stripe

    stripe.api_key = settings.STRIPE_SECRET_KEY
    return stripe


def create_payment_intent(
    amount: Decimal,
    currency: str,
    metadata: Optional[dict] = None,
    idempotency_key: Optional[str] = None,
) -> StubPaymentIntent:
    """Create a Stripe PaymentIntent (or a stub if no live key is configured)."""
    stripe_amount = to_stripe_amount(amount, currency)

    if is_stub_key(settings.STRIPE_SECRET_KEY):
        token = secrets.token_hex(12)
        return StubPaymentIntent(
            id=f"pi_stub_{token}",
            client_secret=f"pi_stub_{token}_secret_{secrets.token_hex(8)}",
            amount=stripe_amount,
            currency=currency.lower(),
        )

    stripe = _stripe_client()
    kwargs = {
        "amount": stripe_amount,
        "currency": currency.lower(),
        "automatic_payment_methods": {"enabled": True},
        "metadata": metadata or {},
    }
    request_options = {}
    if idempotency_key:
        request_options["idempotency_key"] = idempotency_key
    intent = stripe.PaymentIntent.create(**kwargs, **request_options)
    return StubPaymentIntent(
        id=intent.id,
        client_secret=intent.client_secret,
        amount=intent.amount,
        currency=intent.currency,
        status=intent.status,
    )


def construct_event(payload: bytes, sig_header: str):
    """Verify a Stripe webhook signature and return the parsed event.

    Raises ``stripe.error.SignatureVerificationError`` on tamper / mismatch
    so the caller can return 400.
    """
    if is_stub_key(settings.STRIPE_WEBHOOK_SECRET):
        # Dev mode: parse-but-don't-verify so curl-style local tests work.
        import json

        data = json.loads(payload)
        return _DictAttr(data)

    stripe = _stripe_client()
    return stripe.Webhook.construct_event(
        payload=payload,
        sig_header=sig_header,
        secret=settings.STRIPE_WEBHOOK_SECRET,
    )


class _DictAttr(dict):
    """Tiny dict-with-attr-access for the dev-mode webhook stub."""

    def __getattr__(self, key):
        try:
            value = self[key]
        except KeyError as exc:
            raise AttributeError(key) from exc
        if isinstance(value, dict):
            return _DictAttr(value)
        return value

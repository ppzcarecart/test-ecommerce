from __future__ import annotations

import logging
from decimal import Decimal

from django.conf import settings
from django.contrib import messages
from django.db import transaction
from django.http import HttpResponse, HttpResponseBadRequest, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods, require_POST

from cart.cart import Cart

from .emails import send_order_confirmation
from .forms import CheckoutForm
from .models import Order, OrderItem, StripeEvent
from .shipping import quote_shipping, quote_tax
from .stripe_client import construct_event, create_payment_intent

logger = logging.getLogger(__name__)


def _quote_totals(cart: Cart, country: str) -> dict:
    subtotal = cart.subtotal
    ship = quote_shipping(country, subtotal)
    tax = (
        Decimal("0")
        if getattr(settings, "STRIPE_TAX_ENABLED", False)
        else quote_tax(country, subtotal + ship.cost)
    )
    return {
        "subtotal": subtotal,
        "shipping": ship.cost,
        "shipping_eta": ship.eta,
        "shipping_is_free": ship.is_free,
        "shipping_free_threshold": ship.free_threshold,
        "tax": tax,
        "total": subtotal + ship.cost + tax,
    }


def _build_order(form: CheckoutForm, cart: Cart, request) -> Order:
    country = form.cleaned_data.get("country") or "US"
    totals = _quote_totals(cart, country)

    order: Order = form.save(commit=False)
    if request.user.is_authenticated:
        order.user = request.user
    order.subtotal = totals["subtotal"]
    order.shipping = totals["shipping"]
    order.tax = totals["tax"]
    order.total = totals["total"]
    order.currency = settings.DEFAULT_CURRENCY
    order.status = Order.Status.PENDING
    order.save()

    for line in cart:
        OrderItem.objects.create(
            order=order,
            variant=line["variant"],
            product_name=line["product"].name,
            variant_name=line["variant"].name,
            sku=line["variant"].sku,
            unit_price=line["price"],
            quantity=line["qty"],
        )
    return order


@require_http_methods(["GET", "POST"])
def checkout(request):
    cart = Cart(request)
    if cart.is_empty:
        messages.info(request, "Your cart is empty.")
        return redirect("catalog:product_list")

    initial = {}
    if request.user.is_authenticated:
        initial["email"] = request.user.email
        default = request.user.addresses.filter(is_default=True).first()
        if default:
            initial.update(
                full_name=default.full_name,
                address_line1=default.address_line1,
                address_line2=default.address_line2,
                city=default.city,
                postal_code=default.postal_code,
                country=default.country,
            )

    form = CheckoutForm(request.POST or None, initial=initial)
    quote = _quote_totals(cart, request.POST.get("country") or initial.get("country") or "US")

    if request.method == "POST" and form.is_valid():
        with transaction.atomic():
            order = _build_order(form, cart, request)
            intent = create_payment_intent(
                amount=order.total,
                currency=order.currency,
                metadata={
                    "order_id": order.pk,
                    "email": order.email,
                    "user_id": getattr(order.user, "id", "") or "",
                },
                idempotency_key=f"order-{order.pk}",
            )
            order.stripe_payment_intent_id = intent.id
            order.stripe_client_secret = intent.client_secret
            order.save(update_fields=["stripe_payment_intent_id", "stripe_client_secret"])
        return redirect("payments:pay", order_id=order.pk)

    return render(
        request,
        "checkout/checkout.html",
        {"form": form, **quote},
    )


def pay(request, order_id):
    order = get_object_or_404(Order, pk=order_id)
    is_stub = (
        order.stripe_client_secret.startswith("pi_stub_")
        if order.stripe_client_secret
        else True
    )
    return render(
        request,
        "checkout/pay.html",
        {
            "order": order,
            "stripe_public_key": settings.STRIPE_PUBLIC_KEY,
            "is_stub": is_stub,
        },
    )


@require_POST
def confirm(request, order_id):
    """Mark an order as paid (dev-only entry point used by the stub UI).

    In a live flow this would never be called — Stripe's webhook is the
    source of truth. We deliberately re-use ``_mark_paid`` so the stub
    path exercises the same inventory-decrement + email code path as
    real payments do.
    """
    order = get_object_or_404(Order, pk=order_id)
    _mark_paid(order)
    Cart(request).clear()
    return redirect(reverse("payments:success", kwargs={"order_id": order.pk}))


def success(request, order_id):
    order = get_object_or_404(Order, pk=order_id)
    return render(request, "checkout/success.html", {"order": order})


# --- Webhook ---------------------------------------------------------------


def _mark_paid(order: Order) -> None:
    """Idempotently mark an order paid: flip status, decrement variant
    inventory once, and send the confirmation email once."""
    with transaction.atomic():
        order.refresh_from_db()
        if order.status != Order.Status.PAID:
            order.status = Order.Status.PAID
            order.save(update_fields=["status", "updated_at"])
        if not order.inventory_decremented_at:
            for item in order.items.select_related("variant").select_for_update():
                variant = item.variant
                # never go negative — clamp at zero
                new = max(0, int(variant.inventory) - int(item.quantity))
                variant.inventory = new
                variant.save(update_fields=["inventory"])
            order.inventory_decremented_at = timezone.now()
            order.save(update_fields=["inventory_decremented_at"])
    # Email is outside the txn — Postmark / SES failures don't void the order.
    send_order_confirmation(order)


@csrf_exempt
@require_POST
def webhook(request):
    """Stripe webhook endpoint with signature verification + idempotency."""
    payload = request.body
    sig_header = request.headers.get("Stripe-Signature", "")

    try:
        event = construct_event(payload, sig_header)
    except Exception as exc:  # SignatureVerificationError, ValueError, etc.
        logger.warning("Stripe webhook rejected: %s", exc)
        return HttpResponseBadRequest("invalid signature")

    event_id = getattr(event, "id", None) or event.get("id") if isinstance(event, dict) else getattr(event, "id", None)
    event_type = getattr(event, "type", None) or (event.get("type") if isinstance(event, dict) else None)

    if not event_id or not event_type:
        return HttpResponseBadRequest("malformed event")

    # Idempotency: if we've already recorded this event, just ack.
    record, created = StripeEvent.objects.get_or_create(
        event_id=event_id,
        defaults={"event_type": event_type, "payload": _to_dict(event)},
    )
    if not created and record.processed_at:
        return JsonResponse({"received": True, "duplicate": True})

    try:
        if event_type == "payment_intent.succeeded":
            data = _to_dict(event).get("data", {}).get("object", {})
            intent_id = data.get("id")
            if intent_id:
                order = Order.objects.filter(stripe_payment_intent_id=intent_id).first()
                if order:
                    _mark_paid(order)
        elif event_type == "payment_intent.payment_failed":
            data = _to_dict(event).get("data", {}).get("object", {})
            intent_id = data.get("id")
            if intent_id:
                Order.objects.filter(stripe_payment_intent_id=intent_id).update(
                    status=Order.Status.FAILED
                )
        elif event_type == "charge.refunded":
            data = _to_dict(event).get("data", {}).get("object", {})
            intent_id = data.get("payment_intent")
            if intent_id:
                Order.objects.filter(stripe_payment_intent_id=intent_id).update(
                    status=Order.Status.REFUNDED
                )
    except Exception as exc:  # pragma: no cover — defensive
        record.error = str(exc)[:1000]
        record.save(update_fields=["error"])
        logger.exception("Failed to process Stripe webhook %s", event_id)
        return HttpResponse(status=500)

    record.processed_at = timezone.now()
    record.save(update_fields=["processed_at"])
    return JsonResponse({"received": True})


def _to_dict(event):
    if hasattr(event, "to_dict_recursive"):
        return event.to_dict_recursive()
    if hasattr(event, "to_dict"):
        return event.to_dict()
    if isinstance(event, dict):
        return event
    # Fallback: best-effort attribute scrape.
    out = {}
    for key in ("id", "type", "data"):
        try:
            out[key] = getattr(event, key)
        except Exception:
            pass
    return out

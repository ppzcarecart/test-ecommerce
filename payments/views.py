from decimal import Decimal

from django.conf import settings
from django.contrib import messages
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_http_methods, require_POST

from cart.cart import Cart

from .forms import CheckoutForm
from .models import Order, OrderItem
from .stripe_client import create_payment_intent


SHIPPING_FLAT = Decimal("12.00")


def _build_order(form: CheckoutForm, cart: Cart) -> Order:
    order: Order = form.save(commit=False)
    order.subtotal = cart.subtotal
    order.shipping = SHIPPING_FLAT if not cart.is_empty else Decimal("0")
    order.total = order.subtotal + order.shipping
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

    form = CheckoutForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        with transaction.atomic():
            order = _build_order(form, cart)
            intent = create_payment_intent(
                amount=order.total,
                currency=order.currency,
                metadata={"order_id": order.pk, "email": order.email},
            )
            order.stripe_payment_intent_id = intent.id
            order.stripe_client_secret = intent.client_secret
            order.save(update_fields=["stripe_payment_intent_id", "stripe_client_secret"])
        return redirect("payments:pay", order_id=order.pk)

    return render(
        request,
        "checkout/checkout.html",
        {
            "form": form,
            "shipping": SHIPPING_FLAT,
            "subtotal": cart.subtotal,
            "total": cart.subtotal + (SHIPPING_FLAT if not cart.is_empty else Decimal("0")),
        },
    )


def pay(request, order_id):
    order = get_object_or_404(Order, pk=order_id)
    return render(
        request,
        "checkout/pay.html",
        {
            "order": order,
            "stripe_public_key": settings.STRIPE_PUBLIC_KEY,
            "is_stub": order.stripe_client_secret.startswith("pi_stub_")
            if order.stripe_client_secret
            else True,
        },
    )


@require_POST
def confirm(request, order_id):
    """Mark an order as paid. In the stub flow this is fired from the success
    button on the payment page; in a live flow this would be triggered by a
    Stripe webhook (see ``webhook`` below for the real entry point)."""
    order = get_object_or_404(Order, pk=order_id)
    order.status = Order.Status.PAID
    order.save(update_fields=["status"])
    Cart(request).clear()
    return redirect(reverse("payments:success", kwargs={"order_id": order.pk}))


def success(request, order_id):
    order = get_object_or_404(Order, pk=order_id)
    return render(request, "checkout/success.html", {"order": order})


@require_POST
def webhook(request):
    """Stripe webhook stub. Wire up signature verification when going live."""
    # Placeholder so the URL exists and ngrok-style integrations can be tested.
    from django.http import JsonResponse

    return JsonResponse({"received": True})

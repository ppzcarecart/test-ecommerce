from django.contrib import messages
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_POST

from catalog.models import ProductVariant

from .cart import Cart


def cart_detail(request):
    return render(request, "cart/cart_detail.html")


@require_POST
def cart_add(request, variant_id):
    variant = get_object_or_404(ProductVariant, id=variant_id, is_active=True)
    cart = Cart(request)
    try:
        quantity = max(1, int(request.POST.get("qty", 1)))
    except ValueError:
        quantity = 1
    cart.add(variant=variant, quantity=quantity)
    messages.success(request, f"Added {variant.name} to your cart.")
    next_url = request.POST.get("next") or reverse("cart:detail")
    return HttpResponseRedirect(next_url)


@require_POST
def cart_update(request, variant_id):
    cart = Cart(request)
    try:
        quantity = int(request.POST.get("qty", 1))
    except ValueError:
        quantity = 1
    cart.update_quantity(variant_id, quantity)
    return redirect("cart:detail")


@require_POST
def cart_remove(request, variant_id):
    cart = Cart(request)
    cart.remove(variant_id)
    messages.info(request, "Removed from cart.")
    return redirect("cart:detail")

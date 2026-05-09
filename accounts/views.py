from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from catalog.models import Product
from payments.models import Order

from .models import Address, WishlistItem


@login_required
def dashboard(request):
    orders = Order.objects.filter(user=request.user).order_by("-created_at")[:20]
    addresses = request.user.addresses.all()
    wishlist = (
        request.user.wishlist.select_related("product", "product__category")
        .all()[:20]
    )
    return render(
        request,
        "accounts/dashboard.html",
        {"orders": orders, "addresses": addresses, "wishlist": wishlist},
    )


@login_required
@require_POST
def wishlist_toggle(request, product_id):
    product = get_object_or_404(Product, pk=product_id, is_active=True)
    item = WishlistItem.objects.filter(user=request.user, product=product).first()
    if item:
        item.delete()
    else:
        WishlistItem.objects.create(user=request.user, product=product)
    next_url = request.POST.get("next") or product.get_absolute_url()
    return redirect(next_url)


@login_required
def addresses(request):
    if request.method == "POST":
        Address.objects.create(
            user=request.user,
            full_name=request.POST.get("full_name", "")[:200],
            address_line1=request.POST.get("address_line1", "")[:255],
            address_line2=request.POST.get("address_line2", "")[:255],
            city=request.POST.get("city", "")[:120],
            postal_code=request.POST.get("postal_code", "")[:32],
            country=request.POST.get("country", "US")[:64],
            is_default=bool(request.POST.get("is_default")),
        )
        return redirect("accounts:addresses")
    return render(
        request,
        "accounts/addresses.html",
        {"addresses": request.user.addresses.all()},
    )


@login_required
@require_POST
def address_delete(request, pk):
    addr = get_object_or_404(Address, pk=pk, user=request.user)
    addr.delete()
    return redirect("accounts:addresses")

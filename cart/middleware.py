"""Merge the session cart into the user's persistent cart on login."""
from __future__ import annotations

from django.utils.deprecation import MiddlewareMixin


class CartMergeMiddleware(MiddlewareMixin):
    """When a previously-anonymous request becomes authenticated, fold the
    session cart into the user's saved cart and replace the session contents
    with the merged result. Idempotent — a flag in the session prevents the
    merge from running twice for the same login."""

    def process_request(self, request):
        if not getattr(request, "user", None) or not request.user.is_authenticated:
            return None
        flag_key = "_cart_merged_for_user"
        if request.session.get(flag_key) == request.user.id:
            return None
        try:
            from .cart import Cart
        except Exception:  # pragma: no cover — defensive during boot
            return None
        try:
            cart = Cart(request)
            cart.merge_on_login(request.user)
            request.session[flag_key] = request.user.id
        except Exception:  # pragma: no cover — never block a request on merge
            return None
        return None

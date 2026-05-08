from .cart import Cart


def cart(request):
    """Make the cart available in every template as `cart`."""
    return {"cart": Cart(request)}

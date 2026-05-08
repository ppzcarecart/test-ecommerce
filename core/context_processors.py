from django.conf import settings


def site(request):
    """Expose brand + currency + top-level navigation to every template."""
    # Lazy import: avoid circular imports during early Django startup.
    try:
        from catalog.models import Category

        nav_categories = list(
            Category.objects.filter(is_active=True).order_by("position", "name")[:4]
        )
    except Exception:
        # During makemigrations / before catalog migrations are applied.
        nav_categories = []

    return {
        "SITE_NAME": getattr(settings, "SITE_NAME", "LiveBoutique"),
        "SITE_TAGLINE": getattr(settings, "SITE_TAGLINE", "Curated luxury goods"),
        "DEFAULT_CURRENCY": getattr(settings, "DEFAULT_CURRENCY", "USD"),
        "STRIPE_PUBLIC_KEY": getattr(settings, "STRIPE_PUBLIC_KEY", ""),
        "nav_categories": nav_categories,
    }

from django.conf import settings


def site(request):
    """Expose brand + currency + top-level navigation to every template."""
    try:
        from catalog.models import Category

        nav_categories = list(
            Category.objects.filter(is_active=True).order_by("position", "name")[:4]
        )
    except Exception:
        nav_categories = []

    return {
        "SITE_NAME": getattr(settings, "SITE_NAME", "LiveBoutique"),
        "SITE_TAGLINE": getattr(settings, "SITE_TAGLINE", "Curated luxury goods"),
        "SITE_BASE_URL": getattr(settings, "SITE_BASE_URL", ""),
        "DEFAULT_CURRENCY": getattr(settings, "DEFAULT_CURRENCY", "USD"),
        "STRIPE_PUBLIC_KEY": getattr(settings, "STRIPE_PUBLIC_KEY", ""),
        "POSTHOG_API_KEY": getattr(settings, "POSTHOG_API_KEY", ""),
        "POSTHOG_HOST": getattr(settings, "POSTHOG_HOST", ""),
        "nav_categories": nav_categories,
    }

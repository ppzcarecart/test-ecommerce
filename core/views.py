from django.http import HttpResponse
from django.shortcuts import render
from django.template.loader import render_to_string
from django.views.decorators.cache import cache_page

from catalog.models import Category, Product


@cache_page(60)
def home(request):
    featured = (
        Product.objects.filter(is_active=True, is_featured=True)
        .select_related("category")
        .prefetch_related("variants", "images")[:6]
    )
    categories = Category.objects.filter(is_active=True).order_by("position", "name")[:6]
    return render(
        request,
        "core/home.html",
        {"featured": featured, "categories": categories},
    )


def offline(request):
    return render(request, "pwa/offline.html")


def service_worker(request):
    """Render the service worker with the current top-12 product image URLs
    interpolated, so the SW can pre-cache them on install and stay useful
    offline."""
    images = list(
        Product.objects.filter(is_active=True)
        .exclude(image__exact="")
        .order_by("-is_featured", "-created_at")
        .values_list("image", flat=True)[:12]
    )
    body = render_to_string(
        "pwa/sw.js", {"featured_image_urls": images}, request=request
    )
    return HttpResponse(body, content_type="application/javascript")


def robots_txt(request):
    lines = [
        "User-agent: *",
        "Allow: /",
        "Disallow: /admin/",
        "Disallow: /accounts/",
        "Disallow: /account/",
        "Disallow: /cart/",
        "Disallow: /checkout/",
        f"Sitemap: {request.scheme}://{request.get_host()}/sitemap.xml",
    ]
    return HttpResponse("\n".join(lines) + "\n", content_type="text/plain")

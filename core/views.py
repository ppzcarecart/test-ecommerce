from django.shortcuts import render

from catalog.models import Category, Product


def home(request):
    featured = (
        Product.objects.filter(is_active=True, is_featured=True)
        .select_related("category")
        .prefetch_related("variants")[:6]
    )
    categories = Category.objects.filter(is_active=True).order_by("position", "name")[:6]
    return render(
        request,
        "core/home.html",
        {"featured": featured, "categories": categories},
    )


def offline(request):
    return render(request, "pwa/offline.html")

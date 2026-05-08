from django.shortcuts import get_object_or_404, render

from .models import Category, Product


def product_list(request):
    products = (
        Product.objects.filter(is_active=True)
        .select_related("category")
        .prefetch_related("variants")
    )
    categories = Category.objects.filter(is_active=True)
    return render(
        request,
        "catalog/product_list.html",
        {"products": products, "categories": categories, "active_category": None},
    )


def category_detail(request, slug):
    category = get_object_or_404(Category, slug=slug, is_active=True)
    products = (
        category.products.filter(is_active=True)
        .select_related("category")
        .prefetch_related("variants")
    )
    categories = Category.objects.filter(is_active=True)
    return render(
        request,
        "catalog/product_list.html",
        {"products": products, "categories": categories, "active_category": category},
    )


def product_detail(request, slug):
    product = get_object_or_404(
        Product.objects.select_related("category").prefetch_related("variants"),
        slug=slug,
        is_active=True,
    )
    return render(request, "catalog/product_detail.html", {"product": product})

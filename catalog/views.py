"""Catalog views — list with search/filter/sort, PDP with gallery + related."""
from __future__ import annotations

from decimal import Decimal, InvalidOperation

from django.conf import settings
from django.db.models import Min, Q
from django.shortcuts import get_object_or_404, render
from django.views.decorators.cache import cache_page

from .models import Category, Product

CACHE_TIMEOUT = 60  # seconds — short, since pricing/stock can change

SORT_OPTIONS = {
    "newest": ("-created_at",),
    "featured": ("-is_featured", "name"),
    "price_asc": ("min_price", "name"),
    "price_desc": ("-min_price", "name"),
    "name": ("name",),
}


def _filter_queryset(request, base_qs):
    """Apply ?q=, ?category=, ?min_price=, ?max_price=, ?sort= to a queryset."""
    qs = base_qs.select_related("category").prefetch_related("variants").annotate(
        min_price=Min("variants__price")
    )

    q = (request.GET.get("q") or "").strip()
    if q:
        # Use Postgres SearchVector when available; sqlite falls back to icontains.
        engine = settings.DATABASES["default"]["ENGINE"]
        if "postgresql" in engine:
            from django.contrib.postgres.search import SearchQuery, SearchVector

            qs = qs.annotate(
                search=SearchVector("name", "short_description", "description")
            ).filter(search=SearchQuery(q))
        else:
            qs = qs.filter(
                Q(name__icontains=q)
                | Q(short_description__icontains=q)
                | Q(description__icontains=q)
                | Q(category__name__icontains=q)
            )

    cat_slugs = request.GET.getlist("category")
    if cat_slugs:
        qs = qs.filter(category__slug__in=cat_slugs)

    def _decimal(name):
        raw = (request.GET.get(name) or "").strip()
        if not raw:
            return None
        try:
            return Decimal(raw)
        except (InvalidOperation, ValueError):
            return None

    minp = _decimal("min_price")
    maxp = _decimal("max_price")
    if minp is not None:
        qs = qs.filter(min_price__gte=minp)
    if maxp is not None:
        qs = qs.filter(min_price__lte=maxp)

    sort = request.GET.get("sort") or "featured"
    qs = qs.order_by(*SORT_OPTIONS.get(sort, SORT_OPTIONS["featured"]))
    return qs, {"q": q, "sort": sort, "min_price": minp, "max_price": maxp, "category_slugs": cat_slugs}


def _shop_context(request, base_qs, active_category=None, page_title=None):
    products, applied = _filter_queryset(request, base_qs)
    categories = Category.objects.filter(is_active=True)
    return {
        "products": products,
        "categories": categories,
        "active_category": active_category,
        "applied": applied,
        "sort_options": [
            ("featured", "Featured"),
            ("newest", "Newest"),
            ("price_asc", "Price · low to high"),
            ("price_desc", "Price · high to low"),
            ("name", "A → Z"),
        ],
        "page_title": page_title,
        "result_count": products.count(),
    }


@cache_page(CACHE_TIMEOUT)
def product_list(request):
    base = Product.objects.filter(is_active=True)
    ctx = _shop_context(request, base, page_title="The Boutique")
    return render(request, "catalog/product_list.html", ctx)


def category_detail(request, slug):
    category = get_object_or_404(Category, slug=slug, is_active=True)
    base = category.products.filter(is_active=True)
    ctx = _shop_context(
        request, base, active_category=category, page_title=category.name
    )
    return render(request, "catalog/product_list.html", ctx)


def product_detail(request, slug):
    product = get_object_or_404(
        Product.objects.select_related("category")
        .prefetch_related("variants", "images"),
        slug=slug,
        is_active=True,
    )
    related = (
        Product.objects.filter(is_active=True, category=product.category)
        .exclude(pk=product.pk)
        .prefetch_related("variants")[:4]
    )
    in_wishlist = False
    if request.user.is_authenticated:
        in_wishlist = product.wishlisted_by.filter(user=request.user).exists()
    return render(
        request,
        "catalog/product_detail.html",
        {"product": product, "related": related, "in_wishlist": in_wishlist},
    )


def search(request):
    """Search-only entry point used by the header search bar."""
    base = Product.objects.filter(is_active=True)
    ctx = _shop_context(request, base, page_title="Search")
    ctx["is_search"] = True
    return render(request, "catalog/product_list.html", ctx)

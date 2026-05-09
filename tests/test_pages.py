"""Smoke tests: every key page returns 200 for every seeded product."""
from __future__ import annotations

from decimal import Decimal

import pytest
from django.urls import reverse


@pytest.fixture
def seeded(db):
    from catalog.models import Category, Product, ProductVariant

    cats = [
        Category.objects.create(name=n, slug=s, is_active=True, position=i)
        for i, (n, s) in enumerate([
            ("Leather Goods", "leather-goods"),
            ("Timepieces", "timepieces"),
        ])
    ]
    products = []
    for cat in cats:
        for k in range(2):
            p = Product.objects.create(
                category=cat,
                name=f"{cat.name} Item {k}",
                slug=f"{cat.slug}-item-{k}",
                short_description="Test",
                description="Test",
                base_price=Decimal("100.00"),
                is_active=True,
                is_featured=(k == 0),
            )
            ProductVariant.objects.create(
                product=p,
                sku=f"{cat.slug}-item-{k}-A",
                name="A",
                price=Decimal("100.00"),
                inventory=5,
                is_active=True,
            )
            products.append(p)
    return cats, products


@pytest.mark.django_db
def test_home_renders(client, seeded):
    res = client.get(reverse("core:home"))
    assert res.status_code == 200


@pytest.mark.django_db
def test_shop_renders(client, seeded):
    res = client.get(reverse("catalog:product_list"))
    assert res.status_code == 200


@pytest.mark.django_db
def test_search_renders(client, seeded):
    res = client.get(reverse("catalog:search") + "?q=Item")
    assert res.status_code == 200


@pytest.mark.django_db
def test_pdp_renders_for_every_seeded_product(client, seeded):
    _, products = seeded
    for p in products:
        res = client.get(p.get_absolute_url())
        assert res.status_code == 200, f"PDP failed for {p.slug}"
        assert p.name.encode() in res.content


@pytest.mark.django_db
def test_robots_and_sitemap(client, seeded):
    assert client.get("/robots.txt").status_code == 200
    assert client.get("/sitemap.xml").status_code == 200


@pytest.mark.django_db
def test_service_worker_renders(client, seeded):
    res = client.get("/sw.js")
    assert res.status_code == 200
    assert b"liveboutique" in res.content
    assert b"sync-cart-adds" in res.content


@pytest.mark.django_db
def test_manifest_renders(client):
    res = client.get("/manifest.webmanifest")
    assert res.status_code == 200

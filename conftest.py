"""Shared pytest fixtures."""
from __future__ import annotations

from decimal import Decimal

import pytest


@pytest.fixture
def category(db):
    from catalog.models import Category

    return Category.objects.create(
        name="Test Cat", slug="test-cat", is_active=True, position=0
    )


@pytest.fixture
def product(db, category):
    from catalog.models import Product

    return Product.objects.create(
        category=category,
        name="Test Product",
        slug="test-product",
        short_description="short",
        description="desc",
        base_price=Decimal("100.00"),
        is_active=True,
    )


@pytest.fixture
def variant(db, product):
    from catalog.models import ProductVariant

    return ProductVariant.objects.create(
        product=product,
        sku="TEST-A",
        name="A",
        price=Decimal("100.00"),
        inventory=10,
        is_active=True,
    )


@pytest.fixture
def variant_b(db, product):
    from catalog.models import ProductVariant

    return ProductVariant.objects.create(
        product=product,
        sku="TEST-B",
        name="B",
        price=Decimal("120.00"),
        inventory=5,
        is_active=True,
    )

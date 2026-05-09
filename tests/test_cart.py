"""Cart add / update / remove behaviour."""

import pytest
from django.urls import reverse


@pytest.mark.django_db
def test_cart_add(client, variant):
    res = client.post(reverse("cart:add", args=[variant.id]), {"qty": 2})
    assert res.status_code in (302, 303)

    detail = client.get(reverse("cart:detail"))
    assert detail.status_code == 200
    assert variant.product.name.encode() in detail.content


@pytest.mark.django_db
def test_cart_update(client, variant):
    client.post(reverse("cart:add", args=[variant.id]), {"qty": 1})
    res = client.post(reverse("cart:update", args=[variant.id]), {"qty": 3})
    assert res.status_code in (302, 303)
    # Sanity check via detail page — should now show qty=3 in the input.
    detail = client.get(reverse("cart:detail"))
    assert b'value="3"' in detail.content


@pytest.mark.django_db
def test_cart_remove(client, variant):
    client.post(reverse("cart:add", args=[variant.id]), {"qty": 1})
    res = client.post(reverse("cart:remove", args=[variant.id]))
    assert res.status_code in (302, 303)
    # After removal, the variant SKU should not appear.
    detail = client.get(reverse("cart:detail"))
    assert variant.sku.encode() not in detail.content


@pytest.mark.django_db
def test_cart_caps_at_inventory(client, variant):
    # variant.inventory == 10
    client.post(reverse("cart:add", args=[variant.id]), {"qty": 999})
    detail = client.get(reverse("cart:detail"))
    # qty input should be 10, not 999
    assert b'value="10"' in detail.content

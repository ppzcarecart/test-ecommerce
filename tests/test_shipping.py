from decimal import Decimal

from payments.shipping import quote_shipping, quote_tax


def test_us_subtotal_below_threshold_charges_flat():
    q = quote_shipping("US", Decimal("100"))
    assert q.cost == Decimal("12.00")
    assert q.is_free is False


def test_us_subtotal_above_threshold_is_free():
    q = quote_shipping("US", Decimal("500"))
    assert q.cost == Decimal("0")
    assert q.is_free is True


def test_eu_country_normalised():
    q = quote_shipping("DE", Decimal("100"))
    assert q.cost == Decimal("30.00")


def test_unknown_country_falls_back_to_default():
    q = quote_shipping("ZZ", Decimal("100"))
    assert q.cost == Decimal("48.00")


def test_tax_rates():
    assert quote_tax("US", Decimal("100")) == Decimal("7.50")
    assert quote_tax("GB", Decimal("100")) == Decimal("20.00")
    assert quote_tax("DE", Decimal("100")) == Decimal("21.00")

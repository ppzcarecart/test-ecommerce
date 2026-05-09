"""Flat-rate shipping table + simple destination-based tax estimate.

Real fulfillment teams will replace this with a Shippo / EasyPost / carrier
quote. The shape stays identical: a country code in, a (cost, label) tuple out.
"""
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

# (rate_in_USD, ETA_label, free_threshold)
_FLAT_TABLE: dict[str, tuple[Decimal, str, Decimal]] = {
    "US": (Decimal("12.00"), "3–5 business days", Decimal("250")),
    "CA": (Decimal("22.00"), "5–8 business days", Decimal("400")),
    "GB": (Decimal("30.00"), "5–8 business days", Decimal("500")),
    "EU": (Decimal("30.00"), "5–8 business days", Decimal("500")),
    "JP": (Decimal("38.00"), "7–10 business days", Decimal("600")),
    "AU": (Decimal("42.00"), "7–10 business days", Decimal("600")),
}
# Anything outside the table falls back to the highest tier.
_DEFAULT = (Decimal("48.00"), "10–14 business days", Decimal("750"))

_EU_COUNTRIES = {
    "AT", "BE", "BG", "HR", "CY", "CZ", "DK", "EE", "FI", "FR", "DE", "GR",
    "HU", "IE", "IT", "LV", "LT", "LU", "MT", "NL", "PL", "PT", "RO", "SK",
    "SI", "ES", "SE",
}


@dataclass(frozen=True)
class ShippingQuote:
    cost: Decimal
    eta: str
    is_free: bool
    free_threshold: Decimal


def quote_shipping(country: str, subtotal: Decimal) -> ShippingQuote:
    code = (country or "US").upper().strip()
    if code in _EU_COUNTRIES:
        code = "EU"
    rate, eta, free = _FLAT_TABLE.get(code, _DEFAULT)
    if subtotal >= free:
        return ShippingQuote(cost=Decimal("0"), eta=eta, is_free=True, free_threshold=free)
    return ShippingQuote(cost=rate, eta=eta, is_free=False, free_threshold=free)


# --- Tax ---------------------------------------------------------------

# Rough destination-based estimate when Stripe Tax isn't enabled. NOT an
# accurate compliance tool — surface it as "estimated tax" in the UI.
_TAX_RATES = {
    "US": Decimal("0.075"),
    "CA": Decimal("0.13"),
    "GB": Decimal("0.20"),
    "EU": Decimal("0.21"),
    "JP": Decimal("0.10"),
    "AU": Decimal("0.10"),
}


def quote_tax(country: str, taxable_amount: Decimal) -> Decimal:
    code = (country or "US").upper().strip()
    if code in _EU_COUNTRIES:
        code = "EU"
    rate = _TAX_RATES.get(code, Decimal("0"))
    return (taxable_amount * rate).quantize(Decimal("0.01"))

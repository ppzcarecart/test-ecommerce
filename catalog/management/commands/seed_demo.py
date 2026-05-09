"""Seed the storefront with categories, products, and variants for demo data.

Idempotent — uses get_or_create so re-running is safe.
"""
from decimal import Decimal

from django.core.management.base import BaseCommand

from catalog.models import Category, Product, ProductVariant

CATEGORIES = [
    {
        "name": "Leather Goods",
        "slug": "leather-goods",
        "description": "Heritage-craft bags and accessories.",
        "hero_image": "https://images.unsplash.com/photo-1548036328-c9fa89d128fa?w=1200",
        "position": 1,
    },
    {
        "name": "Timepieces",
        "slug": "timepieces",
        "description": "Mechanical watches for considered wrists.",
        "hero_image": "https://images.unsplash.com/photo-1524592094714-0f0654e20314?w=1200",
        "position": 2,
    },
    {
        "name": "Fragrance",
        "slug": "fragrance",
        "description": "Perfumes blended in small batches.",
        "hero_image": "https://images.unsplash.com/photo-1541643600914-78b084683601?w=1200",
        "position": 3,
    },
    {
        "name": "Home",
        "slug": "home",
        "description": "Quiet luxury for the spaces you live in.",
        "hero_image": "https://images.unsplash.com/photo-1505691938895-1758d7feb511?w=1200",
        "position": 4,
    },
]


PRODUCTS = [
    {
        "category": "leather-goods",
        "name": "Onyx Tote",
        "slug": "onyx-tote",
        "short_description": "Hand-finished full-grain leather, made in Florence.",
        "description": (
            "A weekday tote cut from full-grain Italian leather, hand-burnished and "
            "finished with solid brass hardware. The interior is lined in twill and "
            "finished with a removable zipped pouch."
        ),
        "base_price": Decimal("780.00"),
        "image": "https://images.unsplash.com/photo-1547949003-9792a18a2601?w=1200",
        "is_featured": True,
        "variants": [
            {"sku": "TOTE-ONX-S", "name": "Onyx · Small", "price": "780.00", "inventory": 12},
            {"sku": "TOTE-ONX-L", "name": "Onyx · Large", "price": "920.00", "inventory": 6},
            {"sku": "TOTE-CGN-L", "name": "Cognac · Large", "price": "920.00", "inventory": 4},
        ],
    },
    {
        "category": "leather-goods",
        "name": "Bond Card Holder",
        "slug": "bond-card-holder",
        "short_description": "A slim card case in vegetable-tanned leather.",
        "description": "Six card slots and a centre pocket, finished by hand in Spain.",
        "base_price": Decimal("180.00"),
        "image": "https://images.unsplash.com/photo-1606760227091-3dd870d97f1d?w=1200",
        "is_featured": False,
        "variants": [
            {"sku": "CARD-BLK", "name": "Jet Black", "price": "180.00", "inventory": 30},
            {"sku": "CARD-OXB", "name": "Oxblood", "price": "180.00", "inventory": 20},
        ],
    },
    {
        "category": "timepieces",
        "name": "Meridian Automatic",
        "slug": "meridian-automatic",
        "short_description": "38mm automatic with sapphire case-back.",
        "description": (
            "Swiss Sellita SW200 movement, 38mm brushed steel case, domed sapphire "
            "crystal. Water resistant to 100m."
        ),
        "base_price": Decimal("2400.00"),
        "image": "https://images.unsplash.com/photo-1523275335684-37898b6baf30?w=1200",
        "is_featured": True,
        "variants": [
            {"sku": "MER-STL-BLU", "name": "Steel · Glacier Blue", "price": "2400.00", "inventory": 5},
            {"sku": "MER-STL-SLV", "name": "Steel · Champagne", "price": "2400.00", "inventory": 3},
            {"sku": "MER-GLD-BLK", "name": "Gold · Onyx", "price": "3200.00", "inventory": 2},
        ],
    },
    {
        "category": "fragrance",
        "name": "No. 7 Velvet Oud",
        "slug": "no-7-velvet-oud",
        "short_description": "Smoked oud, rose absolute, vanilla bourbon.",
        "description": (
            "An evening fragrance composed in Grasse: oud wood smoked over cedar, "
            "with rose absolute and a long vanilla drydown."
        ),
        "base_price": Decimal("260.00"),
        "image": "https://images.unsplash.com/photo-1541643600914-78b084683601?w=1200",
        "is_featured": True,
        "variants": [
            {"sku": "FRAG-V7-50", "name": "Eau de Parfum · 50ml", "price": "260.00", "inventory": 25},
            {"sku": "FRAG-V7-100", "name": "Eau de Parfum · 100ml", "price": "390.00", "inventory": 15},
        ],
    },
    {
        "category": "home",
        "name": "Atelier Cashmere Throw",
        "slug": "atelier-cashmere-throw",
        "short_description": "Pure Mongolian cashmere, woven in Italy.",
        "description": "Two-ply cashmere, hand-finished fringe, 130 × 180 cm.",
        "base_price": Decimal("540.00"),
        "image": "https://images.unsplash.com/photo-1505691938895-1758d7feb511?w=1200",
        "is_featured": True,
        "variants": [
            {"sku": "THR-IVY", "name": "Ivory", "price": "540.00", "inventory": 10},
            {"sku": "THR-CHR", "name": "Charcoal", "price": "540.00", "inventory": 8},
            {"sku": "THR-CML", "name": "Camel", "price": "540.00", "inventory": 6},
        ],
    },
    {
        "category": "home",
        "name": "Maison Soy Candle",
        "slug": "maison-soy-candle",
        "short_description": "60-hour burn, hand-poured in small batches.",
        "description": "Soy and coconut wax, double-wick, lead-free cotton.",
        "base_price": Decimal("85.00"),
        "image": "https://images.unsplash.com/photo-1602874801006-2bd96d2e3a37?w=1200",
        "is_featured": False,
        "variants": [
            {"sku": "CDL-FIG", "name": "Black Fig", "price": "85.00", "inventory": 40},
            {"sku": "CDL-VTV", "name": "Vetiver", "price": "85.00", "inventory": 35},
            {"sku": "CDL-AMB", "name": "Amber", "price": "85.00", "inventory": 25},
        ],
    },
]


class Command(BaseCommand):
    help = "Seed categories, products, and variants for the demo storefront."

    def handle(self, *args, **options):
        for cat in CATEGORIES:
            Category.objects.update_or_create(
                slug=cat["slug"],
                defaults={k: v for k, v in cat.items() if k != "slug"},
            )

        for p in PRODUCTS:
            category = Category.objects.get(slug=p["category"])
            product, _ = Product.objects.update_or_create(
                slug=p["slug"],
                defaults={
                    "category": category,
                    "name": p["name"],
                    "short_description": p["short_description"],
                    "description": p["description"],
                    "base_price": p["base_price"],
                    "image": p["image"],
                    "is_featured": p["is_featured"],
                    "is_active": True,
                },
            )
            for v in p.get("variants", []):
                ProductVariant.objects.update_or_create(
                    sku=v["sku"],
                    defaults={
                        "product": product,
                        "name": v["name"],
                        "price": Decimal(v["price"]),
                        "inventory": v["inventory"],
                        "is_active": True,
                    },
                )

        self.stdout.write(self.style.SUCCESS("Seeded categories, products, and variants."))

from decimal import Decimal

from django.db import models
from django.urls import reverse
from django.utils.text import slugify


class Category(models.Model):
    name = models.CharField(max_length=140, unique=True)
    slug = models.SlugField(max_length=160, unique=True)
    description = models.TextField(blank=True)
    hero_image = models.URLField(
        blank=True,
        help_text="Optional remote image URL used on the storefront category card.",
    )
    position = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = "Categories"
        ordering = ("position", "name")

    def __str__(self) -> str:
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def get_absolute_url(self) -> str:
        return reverse("catalog:category", kwargs={"slug": self.slug})


class Product(models.Model):
    category = models.ForeignKey(
        Category, related_name="products", on_delete=models.PROTECT
    )
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=220, unique=True)
    short_description = models.CharField(max_length=255, blank=True)
    description = models.TextField(blank=True)
    base_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal("0.00"),
        help_text="Used when the product has no variants, or as a fallback display price.",
    )
    image = models.URLField(
        blank=True,
        help_text="Hero image URL (Unsplash links are fine for the seed data).",
    )
    is_active = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-is_featured", "name")
        indexes = [models.Index(fields=["slug"]), models.Index(fields=["is_active"])]

    def __str__(self) -> str:
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def get_absolute_url(self) -> str:
        return reverse("catalog:product", kwargs={"slug": self.slug})

    @property
    def display_price(self) -> Decimal:
        first_variant = self.variants.filter(is_active=True).order_by("price").first()
        if first_variant:
            return first_variant.price
        return self.base_price

    @property
    def has_variants(self) -> bool:
        return self.variants.filter(is_active=True).exists()


class ProductVariant(models.Model):
    """A purchasable variant of a product (e.g. size/colour combo)."""

    product = models.ForeignKey(
        Product, related_name="variants", on_delete=models.CASCADE
    )
    sku = models.CharField(max_length=64, unique=True)
    name = models.CharField(
        max_length=140,
        help_text="Human-readable variant label, e.g. 'Onyx · Large'.",
    )
    price = models.DecimalField(max_digits=10, decimal_places=2)
    inventory = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ("price",)

    def __str__(self) -> str:
        return f"{self.product.name} — {self.name}"

    @property
    def in_stock(self) -> bool:
        return self.is_active and self.inventory > 0

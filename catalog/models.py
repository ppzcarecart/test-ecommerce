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


class ProductManager(models.Manager):
    """Default manager hides soft-deleted (``is_deleted=True``) rows."""

    def get_queryset(self):
        return super().get_queryset().filter(is_deleted=False)


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
    # Soft-delete: keeps order history intact while hiding from the storefront.
    is_deleted = models.BooleanField(default=False, db_index=True)
    deleted_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = ProductManager()
    all_objects = models.Manager()  # bypasses the soft-delete filter

    class Meta:
        ordering = ("-is_featured", "name")
        indexes = [
            models.Index(fields=["slug"]),
            models.Index(fields=["is_active"]),
        ]

    def __str__(self) -> str:
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def soft_delete(self):
        from django.utils import timezone

        self.is_deleted = True
        self.is_active = False
        self.deleted_at = timezone.now()
        self.save(update_fields=["is_deleted", "is_active", "deleted_at"])

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

    @property
    def total_inventory(self) -> int:
        return sum(
            (v.inventory for v in self.variants.filter(is_active=True)),
            0,
        )

    @property
    def is_sold_out(self) -> bool:
        if self.has_variants:
            return self.total_inventory == 0
        return False

    @property
    def is_low_stock(self) -> bool:
        return 0 < self.total_inventory <= 3

    @property
    def primary_image_url(self) -> str:
        first = self.images.order_by("position").first()
        if first and first.url:
            return first.url
        return self.image


class ProductImage(models.Model):
    product = models.ForeignKey(
        Product, related_name="images", on_delete=models.CASCADE
    )
    url = models.URLField(help_text="Image URL — supports remote (Unsplash etc.) or /media/ uploads.")
    alt = models.CharField(max_length=255, blank=True)
    position = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ("position", "id")

    def __str__(self) -> str:
        return f"{self.product.name} #{self.position}"


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
    # ``inventory`` is the canonical stock counter — mirrored by ``stock``
    # for code that wants the more conventional name.
    inventory = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ("price",)

    def __str__(self) -> str:
        return f"{self.product.name} — {self.name}"

    @property
    def stock(self) -> int:
        return self.inventory

    @property
    def in_stock(self) -> bool:
        return self.is_active and self.inventory > 0

    @property
    def is_low_stock(self) -> bool:
        return 0 < self.inventory <= 3

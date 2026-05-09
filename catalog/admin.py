"""Catalog admin — uses django-unfold for the brand-matched look, plus a CSV
bulk-import action for products + variants."""
from __future__ import annotations

import csv
import io
from decimal import Decimal, InvalidOperation

from django import forms
from django.contrib import admin, messages
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.urls import path
from django.utils.html import format_html
from unfold.admin import ModelAdmin, TabularInline

from .models import Category, Product, ProductImage, ProductVariant


class ProductVariantInline(TabularInline):
    model = ProductVariant
    extra = 1


class ProductImageInline(TabularInline):
    model = ProductImage
    extra = 1


class CSVImportForm(forms.Form):
    csv_file = forms.FileField(
        label="CSV file",
        help_text=(
            "Required columns: category_slug, product_slug, product_name, "
            "variant_sku, variant_name, price, inventory. "
            "Optional: short_description, description, image."
        ),
    )


@admin.register(Category)
class CategoryAdmin(ModelAdmin):
    list_display = ("name", "slug", "position", "is_active")
    list_editable = ("position", "is_active")
    prepopulated_fields = {"slug": ("name",)}
    search_fields = ("name",)


@admin.register(Product)
class ProductAdmin(ModelAdmin):
    list_display = (
        "name",
        "category",
        "base_price",
        "is_featured",
        "is_active",
        "is_deleted",
        "_inventory_badge",
    )
    list_filter = ("category", "is_featured", "is_active", "is_deleted")
    list_editable = ("is_featured", "is_active")
    prepopulated_fields = {"slug": ("name",)}
    search_fields = ("name", "short_description")
    inlines = [ProductImageInline, ProductVariantInline]
    actions = ("soft_delete_action", "restore_action")
    change_list_template = "admin/catalog/product_changelist.html"

    def get_queryset(self, request):
        # Admin shows ALL products including soft-deleted ones.
        return Product.all_objects.all()

    def _inventory_badge(self, obj: Product) -> str:
        total = obj.total_inventory
        if total == 0:
            color = "#ef4444"
            label = "Sold out"
        elif total <= 3:
            color = "#f59e0b"
            label = f"Low ({total})"
        else:
            color = "#10b981"
            label = str(total)
        return format_html(
            '<span style="color:{}; font-weight:600">{}</span>', color, label
        )

    _inventory_badge.short_description = "Stock"

    @admin.action(description="Soft-delete selected products")
    def soft_delete_action(self, request, queryset):
        count = 0
        for product in queryset:
            product.soft_delete()
            count += 1
        self.message_user(
            request,
            f"Soft-deleted {count} product(s).",
            level=messages.SUCCESS,
        )

    @admin.action(description="Restore selected products")
    def restore_action(self, request, queryset):
        count = queryset.update(is_deleted=False, deleted_at=None)
        self.message_user(request, f"Restored {count} product(s).", level=messages.SUCCESS)

    # --- Bulk CSV import -----------------------------------------------

    def get_urls(self):
        urls = super().get_urls()
        custom = [
            path(
                "import-csv/",
                self.admin_site.admin_view(self.import_csv_view),
                name="catalog_product_import_csv",
            ),
        ]
        return custom + urls

    def import_csv_view(self, request):
        if request.method == "POST":
            form = CSVImportForm(request.POST, request.FILES)
            if form.is_valid():
                created, updated, errors = self._ingest_csv(form.cleaned_data["csv_file"])
                self.message_user(
                    request,
                    f"Imported CSV — {created} created, {updated} updated. "
                    + (f"{len(errors)} row(s) skipped." if errors else ""),
                    level=messages.WARNING if errors else messages.SUCCESS,
                )
                if errors:
                    for line, err in errors[:10]:
                        self.message_user(
                            request,
                            f"Row {line}: {err}",
                            level=messages.WARNING,
                        )
                return HttpResponseRedirect("..")
        else:
            form = CSVImportForm()
        return render(
            request,
            "admin/catalog/product_import.html",
            {"form": form, "title": "Import products from CSV"},
        )

    def _ingest_csv(self, fh):
        text = io.StringIO(fh.read().decode("utf-8-sig"))
        reader = csv.DictReader(text)
        created = updated = 0
        errors: list[tuple[int, str]] = []

        for line, row in enumerate(reader, start=2):
            try:
                cat_slug = (row.get("category_slug") or "").strip()
                product_slug = (row.get("product_slug") or "").strip()
                product_name = (row.get("product_name") or "").strip()
                sku = (row.get("variant_sku") or "").strip()
                variant_name = (row.get("variant_name") or "").strip()
                price = Decimal((row.get("price") or "0").strip() or "0")
                inventory = int((row.get("inventory") or "0").strip() or 0)
                if not (cat_slug and product_slug and sku and variant_name):
                    raise ValueError("missing required column")

                category, _ = Category.objects.get_or_create(
                    slug=cat_slug,
                    defaults={"name": cat_slug.replace("-", " ").title()},
                )
                product, p_created = Product.all_objects.get_or_create(
                    slug=product_slug,
                    defaults={
                        "name": product_name or product_slug,
                        "category": category,
                        "base_price": price,
                        "short_description": (row.get("short_description") or "")[:255],
                        "description": row.get("description") or "",
                        "image": row.get("image") or "",
                    },
                )
                if not p_created:
                    product.name = product_name or product.name
                    product.category = category
                    if row.get("image"):
                        product.image = row["image"]
                    product.save()
                _, v_created = ProductVariant.objects.update_or_create(
                    sku=sku,
                    defaults={
                        "product": product,
                        "name": variant_name,
                        "price": price,
                        "inventory": inventory,
                        "is_active": True,
                    },
                )
                if v_created:
                    created += 1
                else:
                    updated += 1
            except (ValueError, InvalidOperation, KeyError) as exc:
                errors.append((line, str(exc)))
        return created, updated, errors


@admin.register(ProductVariant)
class ProductVariantAdmin(ModelAdmin):
    list_display = ("sku", "product", "name", "price", "inventory", "is_active")
    list_filter = ("is_active",)
    search_fields = ("sku", "name", "product__name")


@admin.register(ProductImage)
class ProductImageAdmin(ModelAdmin):
    list_display = ("product", "url", "position", "alt")
    list_filter = ("product__category",)
    search_fields = ("product__name", "alt")

"""Sitemap definitions for the storefront."""
from __future__ import annotations

from django.contrib.sitemaps import Sitemap
from django.urls import reverse

from .models import Category, Product


class StaticSitemap(Sitemap):
    priority = 0.8
    changefreq = "weekly"

    def items(self):
        return ["core:home", "catalog:product_list"]

    def location(self, name: str) -> str:
        return reverse(name)


class CategorySitemap(Sitemap):
    priority = 0.7
    changefreq = "weekly"

    def items(self):
        return Category.objects.filter(is_active=True)


class ProductSitemap(Sitemap):
    priority = 0.9
    changefreq = "weekly"

    def items(self):
        return Product.objects.filter(is_active=True)

    def lastmod(self, obj: Product):
        return obj.updated_at

"""Order admin — Unfold theme, with a CSV export action."""
from __future__ import annotations

import csv

from django.contrib import admin
from django.http import HttpResponse
from unfold.admin import ModelAdmin, TabularInline

from .models import Order, OrderItem, StripeEvent


class OrderItemInline(TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ("product_name", "variant_name", "sku", "unit_price", "quantity")


@admin.register(Order)
class OrderAdmin(ModelAdmin):
    list_display = (
        "id",
        "email",
        "full_name",
        "user",
        "total",
        "currency",
        "status",
        "created_at",
    )
    list_filter = ("status", "currency", "created_at", "country")
    search_fields = (
        "email",
        "full_name",
        "stripe_payment_intent_id",
        "user__email",
    )
    readonly_fields = (
        "stripe_payment_intent_id",
        "stripe_client_secret",
        "confirmation_email_sent_at",
        "inventory_decremented_at",
        "created_at",
        "updated_at",
    )
    inlines = [OrderItemInline]
    actions = ("export_orders_csv",)

    @admin.action(description="Export selected orders as CSV")
    def export_orders_csv(self, request, queryset):
        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = "attachment; filename=orders.csv"
        writer = csv.writer(response)
        writer.writerow([
            "id",
            "created_at",
            "status",
            "email",
            "full_name",
            "country",
            "subtotal",
            "shipping",
            "tax",
            "total",
            "currency",
            "stripe_payment_intent_id",
            "items",
        ])
        for order in queryset.prefetch_related("items"):
            items = "; ".join(
                f"{i.sku}×{i.quantity}@{i.unit_price}" for i in order.items.all()
            )
            writer.writerow([
                order.id,
                order.created_at.isoformat(),
                order.status,
                order.email,
                order.full_name,
                order.country,
                order.subtotal,
                order.shipping,
                order.tax,
                order.total,
                order.currency,
                order.stripe_payment_intent_id,
                items,
            ])
        return response


@admin.register(StripeEvent)
class StripeEventAdmin(ModelAdmin):
    list_display = ("event_id", "event_type", "received_at", "processed_at")
    list_filter = ("event_type",)
    search_fields = ("event_id",)
    readonly_fields = ("event_id", "event_type", "payload", "received_at", "processed_at", "error")

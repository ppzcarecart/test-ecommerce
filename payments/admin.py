from django.contrib import admin

from .models import Order, OrderItem


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ("product_name", "variant_name", "sku", "unit_price", "quantity")


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("id", "email", "full_name", "total", "currency", "status", "created_at")
    list_filter = ("status", "currency", "created_at")
    search_fields = ("email", "full_name", "stripe_payment_intent_id")
    readonly_fields = (
        "stripe_payment_intent_id",
        "stripe_client_secret",
        "created_at",
        "updated_at",
    )
    inlines = [OrderItemInline]

from django.contrib import admin

from .models import Address, WishlistItem


@admin.register(Address)
class AddressAdmin(admin.ModelAdmin):
    list_display = ("user", "full_name", "city", "country", "is_default", "created_at")
    list_filter = ("country", "is_default")
    search_fields = ("user__email", "full_name", "city")


@admin.register(WishlistItem)
class WishlistItemAdmin(admin.ModelAdmin):
    list_display = ("user", "product", "created_at")
    search_fields = ("user__email", "product__name")

from django.urls import path

from . import views

app_name = "accounts"

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("addresses/", views.addresses, name="addresses"),
    path("addresses/<int:pk>/delete/", views.address_delete, name="address_delete"),
    path("wishlist/<int:product_id>/toggle/", views.wishlist_toggle, name="wishlist_toggle"),
]

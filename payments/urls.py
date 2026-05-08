from django.urls import path

from . import views

app_name = "payments"

urlpatterns = [
    path("", views.checkout, name="checkout"),
    path("<int:order_id>/pay/", views.pay, name="pay"),
    path("<int:order_id>/confirm/", views.confirm, name="confirm"),
    path("<int:order_id>/success/", views.success, name="success"),
    path("webhook/", views.webhook, name="webhook"),
]

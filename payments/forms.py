from django import forms

from .models import Order


class CheckoutForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = (
            "email",
            "full_name",
            "address_line1",
            "address_line2",
            "city",
            "postal_code",
            "country",
        )
        widgets = {
            "email": forms.EmailInput(attrs={"autocomplete": "email", "placeholder": "you@example.com"}),
            "full_name": forms.TextInput(attrs={"autocomplete": "name", "placeholder": "Full name"}),
            "address_line1": forms.TextInput(attrs={"autocomplete": "address-line1", "placeholder": "Street address"}),
            "address_line2": forms.TextInput(attrs={"autocomplete": "address-line2", "placeholder": "Apartment, suite, etc. (optional)"}),
            "city": forms.TextInput(attrs={"autocomplete": "address-level2", "placeholder": "City"}),
            "postal_code": forms.TextInput(attrs={"autocomplete": "postal-code", "placeholder": "Postal code"}),
            "country": forms.TextInput(attrs={"autocomplete": "country-name", "placeholder": "Country"}),
        }

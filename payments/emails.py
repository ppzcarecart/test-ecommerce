"""Transactional email — order confirmation receipt."""
from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils import timezone

if TYPE_CHECKING:
    from .models import Order

logger = logging.getLogger(__name__)


def send_order_confirmation(order: "Order") -> None:
    """Render + send the confirmation HTML email. Idempotent — sets
    ``order.confirmation_email_sent_at`` on success and refuses to resend
    if it's already populated."""
    if order.confirmation_email_sent_at:
        return

    ctx = {
        "order": order,
        "items": list(order.items.all()),
        "site_name": getattr(settings, "SITE_NAME", "LiveBoutique"),
        "site_base_url": getattr(settings, "SITE_BASE_URL", ""),
        "currency": order.currency,
    }
    subject = f"Your {ctx['site_name']} order #{order.pk}"
    text_body = render_to_string("emails/order_confirmation.txt", ctx)
    html_body = render_to_string("emails/order_confirmation.html", ctx)

    msg = EmailMultiAlternatives(
        subject=subject,
        body=text_body,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[order.email],
    )
    msg.attach_alternative(html_body, "text/html")
    try:
        msg.send(fail_silently=False)
    except Exception:
        logger.exception("Failed to send order confirmation for order %s", order.pk)
        return

    order.confirmation_email_sent_at = timezone.now()
    order.save(update_fields=["confirmation_email_sent_at"])

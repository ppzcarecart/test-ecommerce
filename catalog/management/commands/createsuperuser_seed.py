"""Idempotently create the seeded admin user from settings/env vars."""
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Create (or refresh) the seeded admin/superuser using settings values."

    def handle(self, *args, **options):
        User = get_user_model()
        username = getattr(settings, "DJANGO_ADMIN_USERNAME", "admin")
        email = getattr(settings, "DJANGO_ADMIN_EMAIL", "admin@example.com")
        password = getattr(settings, "DJANGO_ADMIN_PASSWORD", "ChangeMe123!")

        user, created = User.objects.get_or_create(
            username=username,
            defaults={"email": email, "is_staff": True, "is_superuser": True},
        )
        user.email = email
        user.is_staff = True
        user.is_superuser = True
        user.set_password(password)
        user.save()

        if created:
            self.stdout.write(
                self.style.SUCCESS(f"Created superuser '{username}' <{email}>.")
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(f"Updated existing superuser '{username}' <{email}>.")
            )

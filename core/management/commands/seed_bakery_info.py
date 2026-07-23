from django.conf import settings
from django.core.management.base import BaseCommand

from core.models import BakeryInfo


class Command(BaseCommand):
    """
    Creates the initial BakeryInfo row from BUSINESS_NAME / WHATSAPP_NUMBER
    / etc in .env, so a fresh clone-and-rename deploy doesn't need someone
    to manually type everything into /admin/ before the site is usable.

    Usage: python manage.py seed_bakery_info
    Safe to re-run: does nothing if a BakeryInfo row already exists.
    """

    help = "Seed the initial BakeryInfo row from environment variables."

    def handle(self, *args, **options):
        if BakeryInfo.objects.exists():
            self.stdout.write(self.style.WARNING("BakeryInfo already exists - skipping."))
            return

        BakeryInfo.objects.create(
            name=settings.BUSINESS_NAME,
            location=settings.BUSINESS_LOCATION,
            whatsapp_number=settings.WHATSAPP_NUMBER,
            address=settings.BUSINESS_LOCATION,
            opening_hours="Mon-Fri: 07:00-18:00\nSat-Sun: 08:00-16:00",
            brand_color=settings.BRAND_COLOR,
        )
        self.stdout.write(self.style.SUCCESS("Created initial BakeryInfo. Edit details in /admin/."))

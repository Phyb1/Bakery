"""
core.models

BakeryInfo is a singleton: exactly one row holds every piece of branding
and contact info (name, WhatsApp number, address, hours, logo, colors).
It's injected into every template via core.context_processors.bakery_info,
so templates never hardcode the business name or number - that's what
makes this codebase reusable for "Business #2" with just a data change.
"""
# Lets us use `str | None` annotations below on Python 3.8/3.9, which is
# what many cPanel shared-hosting "Setup Python App" environments offer -
# without this, that syntax raises a TypeError at import time on <3.10.
from __future__ import annotations

import datetime
from urllib.parse import quote

from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone

# Maps 3-letter weekday abbreviations (as produced by strftime('%a')) to
# an index, so we can expand ranges like "Mon-Fri" into individual days.
_WEEKDAY_ORDER = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]


class BakeryInfo(models.Model):
    """
    Singleton model holding branding + contact details for the business.

    Only one instance should ever exist - see clean(). Access it via the
    `bakery` template variable (added by core.context_processors) rather
    than querying it directly in views, unless you specifically need to
    write to it.
    """

    name = models.CharField(max_length=200, default="Samwa Bakery")
    location = models.CharField(
        max_length=200,
        default="Mvurwi, Mashonaland Central",
        help_text="Town/area shown in page titles and meta description.",
    )
    whatsapp_number = models.CharField(
        max_length=20,
        help_text="Format: +263712345678 (include the country code).",
    )
    address = models.TextField(help_text="Full street address shown in the footer.")
    opening_hours = models.TextField(
        help_text=(
            "One rule per line, e.g.:\n"
            "Mon-Fri: 07:00-18:00\n"
            "Sat-Sun: 08:00-16:00"
        )
    )
    logo = models.ImageField(upload_to="branding/", blank=True, null=True)
    brand_color = models.CharField(
        max_length=7,
        default="#d97706",
        help_text="Hex color used for buttons/accents, e.g. #d97706.",
    )

    class Meta:
        verbose_name = "Bakery Info"
        verbose_name_plural = "Bakery Info"

    def __str__(self) -> str:
        return self.name

    def clean(self):
        """Enforce the singleton constraint at the admin/form level."""
        if not self.pk and BakeryInfo.objects.exists():
            raise ValidationError(
                "Only one Bakery Info record is allowed. Edit the existing "
                "one instead of adding a new one."
            )

    def clean_whatsapp(self) -> str:
        """Digits only, no '+' or spaces - the format wa.me links need."""
        return "".join(filter(str.isdigit, self.whatsapp_number))

    def get_whatsapp_link(self, message: str | None = None) -> str:
        """
        Build a wa.me deep link with a URL-encoded, pre-filled message.
        Usage in templates: {{ bakery.get_whatsapp_link }}
        """
        if message is None:
            message = f"Hi, I'd like to order from {self.name}"
        return f"https://wa.me/{self.clean_whatsapp()}?text={quote(message)}"

    def _parse_hours(self) -> dict:
        """
        Parse opening_hours text into {weekday_abbr: (open_time, close_time)}.
        Supports single days ("Sat: 08:00-16:00") and ranges
        ("Mon-Fri: 07:00-18:00"). Unparseable lines are skipped silently -
        better to show as "open" than crash the homepage over a typo.
        """
        hours_map = {}
        for line in self.opening_hours.splitlines():
            line = line.strip()
            if not line or ":" not in line:
                continue
            try:
                day_part, time_part = line.split(":", 1)
                day_part = day_part.strip()
                open_str, close_str = [p.strip() for p in time_part.strip().split("-")]
                open_time = datetime.datetime.strptime(open_str, "%H:%M").time()
                close_time = datetime.datetime.strptime(close_str, "%H:%M").time()
            except (ValueError, IndexError):
                continue

            if "-" in day_part:
                start_day, end_day = [d.strip() for d in day_part.split("-")]
                if start_day not in _WEEKDAY_ORDER or end_day not in _WEEKDAY_ORDER:
                    continue
                start_idx = _WEEKDAY_ORDER.index(start_day)
                end_idx = _WEEKDAY_ORDER.index(end_day)
                for i in range(start_idx, end_idx + 1):
                    hours_map[_WEEKDAY_ORDER[i]] = (open_time, close_time)
            elif day_part in _WEEKDAY_ORDER:
                hours_map[day_part] = (open_time, close_time)

        return hours_map

    def is_open_now(self) -> bool:
        """
        True if the current local time falls within today's opening hours.
        Defaults to True (open) if opening_hours can't be parsed at all,
        so a typo in the admin never silently blocks all WhatsApp orders.
        """
        hours_map = self._parse_hours()
        if not hours_map:
            return True

        now = timezone.localtime()
        today = _WEEKDAY_ORDER[now.weekday()]
        if today not in hours_map:
            return False

        open_time, close_time = hours_map[today]
        return open_time <= now.time() <= close_time

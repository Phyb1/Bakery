"""
products.models

Category / Product for the digital menu. No cart or checkout models here on
purpose - orders are placed by sending a WhatsApp message, not stored in
the database. `is_available` is the only "inventory" concept: a manual
toggle the owner flips in /admin/ to hide sold-out items.
"""
from django.db import models
from django.urls import reverse
from django.utils.text import slugify


class Category(models.Model):
    """
    A menu section, e.g. Buns, Donuts, Cakes, Pastry, Other.
    `order` controls display order on the menu page (lower shows first).
    """

    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=110, unique=True, blank=True)
    order = models.PositiveIntegerField(default=0, help_text="Lower numbers show first on the menu.")

    class Meta:
        ordering = ["order", "name"]
        verbose_name_plural = "Categories"

    def __str__(self) -> str:
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class Product(models.Model):
    """
    A single menu item. `get_whatsapp_text()` builds the pre-filled order
    message used by both the menu grid's quantity picker and the product
    detail page's "Order on WhatsApp" button.
    """

    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name="products")
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=210, unique=True, blank=True)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=8, decimal_places=2)
    image = models.ImageField(
        upload_to="products/",
        help_text="Keep under ~200KB and roughly 800px wide - this site targets 2G/3G networks.",
    )
    is_available = models.BooleanField(default=True, help_text="Untick to hide sold-out items from the menu.")
    is_featured = models.BooleanField(default=False, help_text="Show on the homepage's featured section.")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["category__order", "name"]

    def __str__(self) -> str:
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def get_absolute_url(self) -> str:
        return reverse("products:detail", kwargs={"slug": self.slug})

    def get_whatsapp_text(self, qty: int = 1) -> str:
        """
        Build the plain-text order message for this product at a given
        quantity, e.g.:
        "Hi, I want 2x Chocolate Cake @ $15.00 each. Total $30.00"
        Encoding into a wa.me URL happens in the template via
        {{ bakery.get_whatsapp_link }} or client-side in cart.js.
        """
        total = self.price * qty
        return f"Hi, I want {qty}x {self.name} @ ${self.price} each. Total ${total}"

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
import uuid


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


class Order(models.Model):
    """Server-recorded order request; payment is confirmed manually by staff."""
    ORDER_TYPES = [("delivery", "Delivery"), ("collection", "Collection")]
    STATUSES = [
        ("pending_confirmation", "Pending confirmation"),
        ("confirmed", "Confirmed"),
        ("preparing", "Preparing"),
        ("ready", "Ready for collection"),
        ("out_for_delivery", "Out for delivery"),
        ("completed", "Completed"),
        ("cancelled", "Cancelled"),
    ]
    PAYMENT_STATUSES = [
        ("unpaid", "Unpaid / not yet discussed"),
        ("proof_received", "Proof received; verify manually"),
        ("paid", "Payment verified"),
        ("refunded", "Refunded"),
    ]
    reference = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    customer_name = models.CharField(max_length=120)
    customer_phone = models.CharField(max_length=40)
    order_type = models.CharField(max_length=12, choices=ORDER_TYPES)
    address = models.TextField(blank=True)
    notes = models.TextField(blank=True)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)
    delivery_fee = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default="USD", editable=False)
    status = models.CharField(max_length=24, choices=STATUSES, default="pending_confirmation")
    payment_status = models.CharField(max_length=16, choices=PAYMENT_STATUSES, default="unpaid")
    payment_note = models.TextField(blank=True, help_text="Staff notes for manual payment verification. Never treat customer claims as verified payment.")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.reference} — {self.customer_name}"


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(Product, on_delete=models.PROTECT, related_name="order_items")
    product_name = models.CharField(max_length=200)
    unit_price = models.DecimalField(max_digits=8, decimal_places=2)
    quantity = models.PositiveIntegerField()
    line_total = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        ordering = ["id"]

    def __str__(self):
        return f"{self.quantity} × {self.product_name}"

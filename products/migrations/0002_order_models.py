import uuid
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [("products", "0001_initial")]
    operations = [
        migrations.CreateModel(
            name="Order",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("reference", models.UUIDField(default=uuid.uuid4, editable=False, unique=True)),
                ("customer_name", models.CharField(max_length=120)),
                ("customer_phone", models.CharField(max_length=40)),
                ("order_type", models.CharField(choices=[("delivery", "Delivery"), ("collection", "Collection")], max_length=12)),
                ("address", models.TextField(blank=True)), ("notes", models.TextField(blank=True)),
                ("subtotal", models.DecimalField(decimal_places=2, max_digits=10)),
                ("delivery_fee", models.DecimalField(decimal_places=2, default=0, max_digits=8)),
                ("total", models.DecimalField(decimal_places=2, max_digits=10)),
                ("currency", models.CharField(default="USD", editable=False, max_length=3)),
                ("status", models.CharField(choices=[("pending_confirmation", "Pending confirmation"), ("confirmed", "Confirmed"), ("preparing", "Preparing"), ("ready", "Ready for collection"), ("out_for_delivery", "Out for delivery"), ("completed", "Completed"), ("cancelled", "Cancelled")], default="pending_confirmation", max_length=24)),
                ("payment_status", models.CharField(choices=[("unpaid", "Unpaid / not yet discussed"), ("proof_received", "Proof received; verify manually"), ("paid", "Payment verified"), ("refunded", "Refunded")], default="unpaid", max_length=16)),
                ("payment_note", models.TextField(blank=True, help_text="Staff notes for manual payment verification. Never treat customer claims as verified payment.")),
                ("created_at", models.DateTimeField(auto_now_add=True)), ("updated_at", models.DateTimeField(auto_now=True)),
            ], options={"ordering": ["-created_at"]},
        ),
        migrations.CreateModel(
            name="OrderItem",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("product_name", models.CharField(max_length=200)),
                ("unit_price", models.DecimalField(decimal_places=2, max_digits=8)),
                ("quantity", models.PositiveIntegerField()),
                ("line_total", models.DecimalField(decimal_places=2, max_digits=10)),
                ("order", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="items", to="products.order")),
                ("product", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="order_items", to="products.product")),
            ], options={"ordering": ["id"]},
        ),
    ]

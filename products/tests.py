import json
from decimal import Decimal
from django.test import TestCase
from django.urls import reverse
from core.models import BakeryInfo
from .models import Category, Product, Order, OrderItem


class OrderCreationTests(TestCase):
    def setUp(self):
        self.bakery = BakeryInfo.objects.create(
            name="Test Bakery", location="Mvurwi", whatsapp_number="+263771234567",
            address="Town", opening_hours="Mon-Sun: 00:00-23:59")
        self.category = Category.objects.create(name="Bread")
        self.product = Product.objects.create(category=self.category, name="Loaf", price=Decimal("2.50"), image="")
        self.url = reverse("products:create_order")

    def post_order(self, **overrides):
        payload = {"name": "Test Customer", "phone": "+263771112222", "order_type": "collection",
                   "address": "", "notes": "No sesame", "items": [{"id": self.product.pk, "qty": 2}]}
        payload.update(overrides)
        return self.client.post(self.url, data=json.dumps(payload), content_type="application/json")

    def test_creates_order_and_server_calculates_total(self):
        response = self.post_order()
        self.assertEqual(response.status_code, 201, response.content)
        order = Order.objects.get()
        self.assertEqual(order.subtotal, Decimal("5.00"))
        self.assertEqual(order.total, Decimal("5.00"))
        self.assertEqual(order.payment_status, "unpaid")
        self.assertEqual(order.items.get().quantity, 2)
        self.assertIn("wa.me/263771234567", response.json()["whatsapp_url"])

    def test_ignores_client_supplied_price(self):
        response = self.post_order(items=[{"id": self.product.pk, "qty": 1, "price": "0.01"}])
        self.assertEqual(response.status_code, 201)
        self.assertEqual(Order.objects.get().total, Decimal("2.50"))

    def test_requires_delivery_address(self):
        response = self.post_order(order_type="delivery", address="")
        self.assertEqual(response.status_code, 400)
        self.assertEqual(Order.objects.count(), 0)

    def test_rejects_unavailable_product(self):
        self.product.is_available = False
        self.product.save()
        response = self.post_order()
        self.assertEqual(response.status_code, 409)
        self.assertEqual(Order.objects.count(), 0)

    def test_rejects_invalid_quantity(self):
        response = self.post_order(items=[{"id": self.product.pk, "qty": 0}])
        self.assertEqual(response.status_code, 400)
        self.assertEqual(Order.objects.count(), 0)

    def test_empty_cart_is_rejected(self):
        response = self.post_order(items=[])
        self.assertEqual(response.status_code, 400)

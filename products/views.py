"""
products.views

Menu page uses HTMX for category filtering + search without a full page
reload (small JS footprint, no SPA framework - keeps things fast on
2G/3G). When the request comes from HTMX (`HX-Request` header), only the
product grid partial is returned instead of the whole page, since HTMX
swaps it into place.

The full menu page (not the partial) is cached briefly to cut DB load,
per the "cache menu page for 15min" optimisation - this is safe because
stock/price changes made in /admin/ just take up to 15 minutes to show,
which is an acceptable tradeoff for a small bakery site.
"""
# Lets us use `str | None` annotations below on Python 3.8/3.9, common on
# cPanel shared-hosting Python App environments.
from __future__ import annotations

import json
from decimal import Decimal
from urllib.parse import quote

from core.models import BakeryInfo
from django.db import transaction
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.shortcuts import get_object_or_404, render

from .models import Category, Product



def _get_filtered_products(category_slug: str | None, query: str | None):
    """
    select_related('category') avoids one extra query per product when
    templates access {{ product.category.name }} - important once a menu
    has 50+ items.
    """
    products = Product.objects.filter(is_available=True).select_related("category")

    if category_slug:
        products = products.filter(category__slug=category_slug)

    if query:
        products = products.filter(name__icontains=query)

    return products


def menu(request):
    """
    Full menu page: category chips + search box + product grid.
    Supports ?category=<slug> and ?q=<search term> as plain query params
    so the page works even with JS/HTMX disabled - HTMX just makes the
    same URLs feel instant by swapping the grid in-place.

    Cached per full URL (including query params) for 15 minutes to cut DB
    load - `vary_on_headers("HX-Request")` keeps the full-page response and
    the HTMX-fragment response cached separately instead of one clobbering
    the other. A price/availability edit in /admin/ can take up to 15
    minutes to show, which is an acceptable tradeoff for a small bakery.
    """
    category_slug = request.GET.get("category", "")
    query = request.GET.get("q", "")

    categories = Category.objects.all()
    products = _get_filtered_products(category_slug, query)

    context = {
        "categories": categories,
        "products": products,
        "active_category": category_slug,
        "query": query,
    }

    # HTMX requests only want the fragment that gets swapped into #product-grid.
    if request.headers.get("HX-Request"):
        return render(request, "products/_product_grid.html", context)

    return render(request, "products/menu.html", context)


def detail(request, slug):
    """Single product page with the full-size image and WhatsApp button."""
    product = get_object_or_404(
        Product.objects.select_related("category"), slug=slug, is_available=True
    )

    # Build the product-specific WhatsApp link here (rather than in the
    # template) so we only ever construct one ?text= param - concatenating
    # bakery.get_whatsapp_link's generic message with a second "&text="
    # for the product would produce a URL with two conflicting text params.
    whatsapp_link = None
    bakery = BakeryInfo.objects.first()
    if bakery:
        whatsapp_link = bakery.get_whatsapp_link(product.get_whatsapp_text())

    return render(
        request,
        "products/product_detail.html",
        {"product": product, "whatsapp_link": whatsapp_link},
    )


@require_POST
def create_order(request):
    """Validate cart data and persist an order using authoritative DB prices."""
    from .models import Order, OrderItem

    try:
        payload = json.loads(request.body.decode("utf-8"))
    except (ValueError, UnicodeDecodeError):
        return JsonResponse({"error": "Invalid order data."}, status=400)

    name = str(payload.get("name", "")).strip()[:120]
    phone = str(payload.get("phone", "")).strip()[:40]
    order_type = str(payload.get("order_type", "")).strip().lower()
    address = str(payload.get("address", "")).strip()[:2000]
    notes = str(payload.get("notes", "")).strip()[:2000]
    items = payload.get("items")
    if not name or not phone or order_type not in {"delivery", "collection"}:
        return JsonResponse({"error": "Enter your name, phone number and delivery or collection choice."}, status=400)
    if order_type == "delivery" and not address:
        return JsonResponse({"error": "A delivery address and nearby landmark are required."}, status=400)
    if not isinstance(items, list) or not items or len(items) > 50:
        return JsonResponse({"error": "Your cart is empty or contains too many different products."}, status=400)

    quantities = {}
    try:
        for item in items:
            product_id = int(item.get("id"))
            quantity = int(item.get("qty"))
            if quantity < 1 or quantity > 99:
                raise ValueError
            quantities[product_id] = min(99, quantities.get(product_id, 0) + quantity)
            if quantities[product_id] > 99:
                raise ValueError
    except (AttributeError, TypeError, ValueError):
        return JsonResponse({"error": "One of the product quantities is invalid."}, status=400)

    products = {p.pk: p for p in Product.objects.filter(pk__in=quantities, is_available=True)}
    if len(products) != len(quantities):
        return JsonResponse({"error": "A product is no longer available. Please refresh the menu and try again."}, status=409)

    subtotal = sum((products[pid].price * qty for pid, qty in quantities.items()), Decimal("0.00"))
    # Delivery fee is deliberately zero until the bakery configures its policy.
    delivery_fee = Decimal("0.00")
    total = subtotal + delivery_fee
    with transaction.atomic():
        order = Order.objects.create(
            customer_name=name, customer_phone=phone, order_type=order_type,
            address=address, notes=notes, subtotal=subtotal,
            delivery_fee=delivery_fee, total=total,
        )
        OrderItem.objects.bulk_create([
            OrderItem(order=order, product=products[pid], product_name=products[pid].name,
                      unit_price=products[pid].price, quantity=qty,
                      line_total=products[pid].price * qty)
            for pid, qty in quantities.items()
        ])

    bakery = BakeryInfo.objects.first()
    if not bakery or not bakery.clean_whatsapp():
        # Keep the order in the database for admin follow-up, but don't fabricate a contact link.
        return JsonResponse({"error": "Your order was saved, but the bakery WhatsApp number is not configured. Please call the bakery."}, status=503)

    lines = [f"BAKERY ORDER REQUEST — {order.reference}", "", f"Name: {name}", f"Phone: {phone}",
             f"Order type: {order_type.title()}"]
    lines.append(f"Delivery address: {address}" if order_type == "delivery" else f"Collection note: {address or 'Please confirm collection time'}")
    lines.extend(["", "ITEMS"])
    for pid, qty in quantities.items():
        product = products[pid]
        lines.append(f"{qty} x {product.name} @ ${product.price:.2f} = ${product.price * qty:.2f}")
    lines.extend(["", f"Subtotal: ${subtotal:.2f}", f"Delivery fee: ${delivery_fee:.2f}", f"Order total: ${total:.2f}"])
    if notes:
        lines.append(f"Instructions: {notes}")
    lines.extend(["", "Please confirm availability, delivery fee (if applicable), final total, payment instructions and estimated time. This is pending bakery confirmation; payment is not marked as received."])
    return JsonResponse({"reference": str(order.reference), "total": str(total),
                         "whatsapp_url": f"https://wa.me/{bakery.clean_whatsapp()}?text={quote(chr(10).join(lines))}"}, status=201)

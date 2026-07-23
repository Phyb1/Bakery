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

from core.models import BakeryInfo
from django.shortcuts import get_object_or_404, render
from django.views.decorators.cache import cache_page
from django.views.decorators.vary import vary_on_headers

from .models import Category, Product

MENU_CACHE_SECONDS = 60 * 15  # 15 minutes


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


@cache_page(MENU_CACHE_SECONDS)
@vary_on_headers("HX-Request")
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

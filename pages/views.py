from django.shortcuts import render

from products.models import Product


def home(request):
    """
    Homepage: hero banner (rendered from BakeryInfo via the base template's
    context processor), featured products, and the about/contact footer.
    select_related keeps this to one query even with several featured items.
    """
    featured_products = (
        Product.objects.filter(is_available=True, is_featured=True)
        .select_related("category")[:6]
    )
    return render(request, "pages/home.html", {"featured_products": featured_products})

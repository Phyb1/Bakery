from django.shortcuts import render
from products.models import Product


def home(request):
    featured_products = Product.objects.filter(is_available=True, is_featured=True).select_related("category")[:6]
    return render(request, "pages/home.html", {"featured_products": featured_products})


def faq(request):
    return render(request, "pages/faq.html")

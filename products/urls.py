from django.urls import path

from . import views

app_name = "products"

urlpatterns = [
    path("", views.menu, name="menu"),
    path("orders/create/", views.create_order, name="create_order"),
    path("<slug:slug>/", views.detail, name="detail"),
]

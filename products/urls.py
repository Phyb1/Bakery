from django.urls import path

from . import views

app_name = "products"

urlpatterns = [
    path("", views.menu, name="menu"),
    path("<slug:slug>/", views.detail, name="detail"),
]

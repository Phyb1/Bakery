from django.contrib import admin
from django.utils.html import format_html

from .models import Category, Product


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "order", "product_count")
    prepopulated_fields = {"slug": ("name",)}
    ordering = ("order", "name")
    class Media:
        css = {"all": ("core/css/admin-branding.css",)}

    @admin.display(description="Products")
    def product_count(self, obj):
        return obj.products.count()


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("thumbnail", "name", "category", "price", "is_available", "is_featured")
    list_filter = ("category", "is_available", "is_featured")
    list_editable = ("price", "is_available", "is_featured")
    search_fields = ("name", "description")
    prepopulated_fields = {"slug": ("name",)}
    ordering = ("category", "name")
    list_per_page = 50
    class Media:
        css = {"all": ("core/css/admin-branding.css",)}

    @admin.display(description="Photo")
    def thumbnail(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" style="width:40px;height:40px;object-fit:cover;border-radius:4px;">',
                obj.image.url,
            )
        return "-"


from .models import Order, OrderItem


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    can_delete = False
    readonly_fields = ("product", "product_name", "unit_price", "quantity", "line_total")


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("reference", "customer_name", "customer_phone", "order_type", "total", "status", "payment_status", "created_at")
    list_filter = ("status", "payment_status", "order_type", "created_at")
    search_fields = ("reference", "customer_name", "customer_phone")
    readonly_fields = ("reference", "currency", "subtotal", "delivery_fee", "total", "created_at", "updated_at")
    inlines = [OrderItemInline]
    list_per_page = 50
    class Media:
        css = {"all": ("core/css/admin-branding.css",)}

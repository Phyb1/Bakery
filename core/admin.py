from django.contrib import admin
from django.conf import settings

from .models import BakeryInfo


admin.site.site_header = "Bakery Management"
admin.site.site_title = "Bakery Admin"
admin.site.index_title = "Manage your bakery website"


@admin.register(BakeryInfo)
class BakeryInfoAdmin(admin.ModelAdmin):
    list_display = ("name", "location", "whatsapp_number", "is_open_now")
    class Media:
        css = {"all": ("core/css/admin-branding.css",)}
    fieldsets = (
        ("Branding", {"fields": ("name", "location", "logo", "brand_color")}),
        ("Contact", {"fields": ("whatsapp_number", "address")}),
        ("Hours", {"fields": ("opening_hours",)}),
    )

    @admin.display(boolean=True, description="Open now?")
    def is_open_now(self, obj):
        return obj.is_open_now()

    def has_add_permission(self, request):
        # Enforce singleton in the admin UI too: hide "Add" once one exists.
        return not BakeryInfo.objects.exists()

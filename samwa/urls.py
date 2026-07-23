"""
samwa root URL configuration.
"""
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("pages.urls")),
    path("menu/", include("products.urls")),
]

# --- Why media is served here instead of relying on Apache ---
# On a normal shared-hosting domain, Apache's public_html serves anything
# under /media/ for free. On a cPanel "Setup Python App" subdomain, that
# isn't true: the subdomain's document root is wired straight to Passenger,
# so *every* request - including /media/products/whatever.jpg - is routed
# into this Django process. If we don't add an explicit route for it,
# uploaded product photos 404 in production even though they exist on disk.
#
# STATIC_URL is already handled by WhiteNoise middleware regardless of
# DEBUG (see MIDDLEWARE in settings/base.py), so it doesn't need an entry
# here. MEDIA_URL has no equivalent middleware, so we add it unconditionally
# (not just under `if settings.DEBUG`) because on a cPanel subdomain,
# "production" still needs Django to serve it - there's no other server in
# front of it doing that job.
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

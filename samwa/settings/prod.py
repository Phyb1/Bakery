"""
Production settings for cPanel shared hosting.
Use: DJANGO_SETTINGS_MODULE=samwa.settings.prod

Security model: whitelist only, no wildcards, no "redirect anything to my
domain" middleware. If a request's Host header isn't in ALLOWED_HOSTS,
Django returns 400 on purpose - that's a feature, not a bug to work around.
"""
from decouple import config, Csv

from .base import *  # noqa: F401,F403

DEBUG = False

# 1. WHITELIST ONLY - read from .env, no wildcards.
# .env example: ALLOWED_HOSTS=samwabakery.co.zw,www.samwabakery.co.zw
ALLOWED_HOSTS = config("ALLOWED_HOSTS", cast=Csv())

# 2. CSRF trusted origins must include scheme, e.g.:
# CSRF_TRUSTED_ORIGINS=https://samwabakery.co.zw,https://www.samwabakery.co.zw
CSRF_TRUSTED_ORIGINS = config("CSRF_TRUSTED_ORIGINS", cast=Csv())

# 3. HTTPS/SSL security.
# IMPORTANT: only set FORCE_HTTPS=True in .env once cPanel's "Force HTTPS
# Redirect" / AutoSSL is confirmed working for the (sub)domain. If you flip
# this on before SSL is actually live, you'll get a redirect loop. Ships
# with a safe default of True; override to False in .env during initial
# deploy, then flip back once the padlock is green.
_force_https = config("SECURE_SSL_REDIRECT", default=True, cast=bool)
SECURE_SSL_REDIRECT = _force_https
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# 4. Cookie & header security. Tied to the same flag as #3 above - there's
# no scenario where you'd want secure cookies without also forcing HTTPS.
SESSION_COOKIE_SECURE = _force_https
CSRF_COOKIE_SECURE = _force_https
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = "DENY"

# 5. cPanel puts your Django app *outside* the web-served directory
# (e.g. /home/username/samwa), separate from public_html. Passenger serves
# this app directly, so STATIC_ROOT/MEDIA_ROOT just need to be writable
# paths on disk - WhiteNoise + the fallback in urls.py serve them, Apache
# doesn't need to know about them.
STATIC_ROOT = BASE_DIR / "staticfiles"
MEDIA_ROOT = BASE_DIR / "media"

# 6. Logging to a file cPanel lets you tail/download from File Manager.
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "file": {
            "level": "ERROR",
            "class": "logging.FileHandler",
            "filename": BASE_DIR / "django-error.log",
        },
    },
    "loggers": {
        "django": {
            "handlers": ["file"],
            "level": "ERROR",
            "propagate": True,
        },
    },
}

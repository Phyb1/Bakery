"""
Base settings shared by dev.py and prod.py.

Reusable template pattern:
- All business-specific values (name, WhatsApp number, brand color) live in
  the BakeryInfo model and/or .env, never hardcoded in templates or code.
- To launch "Business #2": clone the repo, copy .env.example -> .env,
  fill in the values, migrate, and add a BakeryInfo row in /admin/.
"""
from pathlib import Path
from decouple import config

# Build paths inside the project like this: BASE_DIR / 'subdir'.
# base.py lives in samwa/settings/, so the project root is 2 levels up.
BASE_DIR = Path(__file__).resolve().parent.parent.parent

SECRET_KEY = config("SECRET_KEY")
DEBUG = config("DEBUG", default=False, cast=bool)

ALLOWED_HOSTS = []  # set explicitly in dev.py / prod.py

# --- Applications ---
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    # WhiteNoise's runserver_nostatic must come before staticfiles so
    # `runserver` doesn't double-serve static files during local dev.
    "whitenoise.runserver_nostatic",
    "django.contrib.staticfiles",
    # Local apps
    "core",
    "products",
    "pages",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    # WhiteNoise serves compressed static files directly from the app
    # process. This matters a lot on cPanel subdomains, where there is
    # no separate Apache document root serving /static/ - every request
    # (including static assets) is routed through Passenger/WSGI.
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "samwa.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                # Makes {{ bakery }} available in every template without
                # passing it manually from every view.
                "core.context_processors.bakery_info",
            ],
        },
    },
]

WSGI_APPLICATION = "samwa.wsgi.application"

# --- Database ---
# SQLite: one file, easy to back up on shared hosting (just download
# db.sqlite3). Fine for a single-bakery, low-traffic site.
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

# --- Password validation ---
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# --- Internationalization ---
LANGUAGE_CODE = "en-us"
TIME_ZONE = "Africa/Harare"
USE_I18N = True
USE_TZ = True

# --- Static & media files ---
# NOTE ON CPANEL SUBDOMAINS:
# When a Django app is deployed as its own cPanel "Setup Python App" on a
# subdomain, ALL requests to that subdomain (including /static/... and
# /media/...) are routed through Passenger to this WSGI app. There is no
# separate public_html serving static files the way there would be for a
# plain PHP site. That's the #1 cause of static/media 404s on cPanel:
# people assume Apache serves /static/ for free, but on a Python-app
# subdomain it doesn't. WhiteNoise (in MIDDLEWARE above) covers STATIC_URL.
# MEDIA_URL (user-uploaded product photos) is handled by root urls.py,
# see samwa/urls.py.
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [BASE_DIR / "static"] if (BASE_DIR / "static").exists() else []
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# --- Business-level defaults, read once at startup, used to seed BakeryInfo
# via `python manage.py seed_bakery_info` (see core/management/commands). ---
BUSINESS_NAME = config("BUSINESS_NAME", default="Samwa Bakery")
BUSINESS_LOCATION = config("BUSINESS_LOCATION", default="Mvurwi, Mashonaland Central")
WHATSAPP_NUMBER = config("WHATSAPP_NUMBER", default="+263000000000")
BRAND_COLOR = config("BRAND_COLOR", default="#d97706")

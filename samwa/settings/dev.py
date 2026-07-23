"""
Local development settings.
Run with: python manage.py runserver --settings=samwa.settings.dev
(or leave DJANGO_SETTINGS_MODULE unset in .env - manage.py defaults to this)
"""
from .base import *  # noqa: F401,F403

DEBUG = True

ALLOWED_HOSTS = ["127.0.0.1", "localhost"]

# Not strictly needed with DEBUG=True + CSRF same-origin defaults, but kept
# explicit so dev mirrors the shape of prod.py.
CSRF_TRUSTED_ORIGINS = ["http://127.0.0.1:8000", "http://localhost:8000"]

# Never enforce HTTPS locally.
SECURE_SSL_REDIRECT = False
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False

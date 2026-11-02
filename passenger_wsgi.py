"""cPanel Passenger WSGI entry point for the Bakery Django project."""
import os
import sys

# Ensure the application root is importable when Passenger starts outside it.
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "samwa.settings.prod")

from django.core.wsgi import get_wsgi_application

application = get_wsgi_application()

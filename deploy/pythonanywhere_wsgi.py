# Paste into the PythonAnywhere WSGI file (Web tab -> "WSGI configuration file").
# Replace USERNAME if your account name differs.
import os
import sys

USERNAME = "hgrqagowziyodev"
PROJECT = f"/home/{USERNAME}/shopping-app-backend"

if PROJECT not in sys.path:
    sys.path.insert(0, PROJECT)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

from django.core.wsgi import get_wsgi_application  # noqa: E402

application = get_wsgi_application()

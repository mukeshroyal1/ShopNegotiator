import os
import sys
import traceback
from pathlib import Path

# Ensure the backend package root is importable on Vercel.
BACKEND_ROOT = Path(__file__).resolve().parent.parent
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

from django.core.wsgi import get_wsgi_application

_django_app = get_wsgi_application()


def application(environ, start_response):
    """Top-level WSGI callable required by Vercel's Django builder."""
    try:
        return _django_app(environ, start_response)
    except Exception:  # noqa: BLE001
        body = ("Unhandled error:\n\n" + traceback.format_exc()).encode("utf-8")
        start_response(
            "500 Internal Server Error",
            [
                ("Content-Type", "text/plain; charset=utf-8"),
                ("Content-Length", str(len(body))),
            ],
        )
        return [body]


# Some adapters also look for `app`.
app = application

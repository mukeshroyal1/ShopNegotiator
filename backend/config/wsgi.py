import os
import sys
import traceback
from pathlib import Path

# Ensure the backend package root is importable on Vercel.
BACKEND_ROOT = Path(__file__).resolve().parent.parent
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

try:
    from django.core.wsgi import get_wsgi_application

    _application = get_wsgi_application()
except Exception:  # noqa: BLE001
    _BOOT_ERROR = traceback.format_exc()

    def application(environ, start_response):  # type: ignore[misc]
        body = ("Django failed to start:\n\n" + _BOOT_ERROR).encode("utf-8")
        start_response(
            "500 Internal Server Error",
            [
                ("Content-Type", "text/plain; charset=utf-8"),
                ("Content-Length", str(len(body))),
            ],
        )
        return [body]

    app = application
else:

    def application(environ, start_response):
        try:
            return _application(environ, start_response)
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

    # Some Vercel Python adapters look for `app`.
    app = application

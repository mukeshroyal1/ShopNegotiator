import os
from pathlib import Path
from urllib.parse import unquote, urlparse

from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", "dev-insecure-change-me")
DEBUG = os.getenv("DJANGO_DEBUG", "true").lower() == "true"
ALLOWED_HOSTS = [
    host.strip()
    for host in os.getenv("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1").split(",")
    if host.strip()
]
# Convenience for Render / similar PaaS when host is passed via env as comma list.
if os.getenv("RENDER_EXTERNAL_HOSTNAME"):
    ALLOWED_HOSTS.append(os.environ["RENDER_EXTERNAL_HOSTNAME"])

INSTALLED_APPS = [
    "django.contrib.contenttypes",
    "django.contrib.auth",
    "django.contrib.sessions",
    "django.contrib.staticfiles",
    "corsheaders",
    "rest_framework",
    "common.apps.CommonConfig",
    "accounts",
    "inventory",
    "suppliers",
    "negotiation",
    "quotes",
    "orders",
    "shopify",
    "dashboard_api",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"
WSGI_APPLICATION = "config.wsgi.application"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
            ],
        },
    },
]


def _database_from_url(url: str) -> dict:
    """Parse DATABASE_URL. Special chars in the password must be percent-encoded."""
    parsed = urlparse(url)
    if parsed.hostname is None:
        raise ValueError(
            "DATABASE_URL could not be parsed. URL-encode special characters in the "
            "password (e.g. / → %2F, @ → %40, ! → %21, # → %23)."
        )

    return {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": unquote(parsed.path.lstrip("/")) or "postgres",
        "USER": unquote(parsed.username or "postgres"),
        "PASSWORD": unquote(parsed.password or ""),
        "HOST": parsed.hostname or "localhost",
        "PORT": str(parsed.port or 5432),
        "OPTIONS": {
            "sslmode": os.getenv("DATABASE_SSLMODE", "require"),
            "connect_timeout": 5,
        },
    }


database_url = os.getenv("DATABASE_URL", "")
if database_url:
    DATABASES = {"default": _database_from_url(database_url)}
else:
    # Local bootstrap without Postgres — swap to DATABASE_URL for real data.
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }

AUTH_PASSWORD_VALIDATORS: list[dict] = []

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

CORS_ALLOWED_ORIGINS = [
    origin.strip()
    for origin in os.getenv("CORS_ALLOWED_ORIGINS", "http://localhost:5173").split(",")
    if origin.strip()
]
CORS_ALLOW_CREDENTIALS = True

SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_JWT_SECRET = os.getenv("SUPABASE_JWT_SECRET", "")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")

SHOPIFY_API_KEY = os.getenv("SHOPIFY_API_KEY", "")
SHOPIFY_API_SECRET = os.getenv("SHOPIFY_API_SECRET", "")
SHOPIFY_SCOPES = os.getenv(
    "SHOPIFY_SCOPES",
    "write_draft_orders,write_inventory,read_inventory,read_locations,"
    "read_orders,write_orders,read_products,write_products",
)
SHOPIFY_API_VERSION = os.getenv("SHOPIFY_API_VERSION", "2024-10")
SHOPIFY_REDIRECT_URI = os.getenv(
    "SHOPIFY_REDIRECT_URI",
    "http://localhost:8000/api/shopify/callback/",
)
# Public HTTPS origin for Shopify webhooks (e.g. https://xxxx.ngrok-free.app).
# Localhost cannot receive webhooks; catalog still auto-refreshes when you open Products.
SHOPIFY_APP_URL = os.getenv("SHOPIFY_APP_URL", "")
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:5173")

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "common.auth.SupabaseJWTAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
}

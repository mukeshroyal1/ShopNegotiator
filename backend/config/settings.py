import os
from pathlib import Path
from urllib.parse import unquote, urlparse

from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent


def _env(name: str, default: str = "") -> str:
    """Read env var; treat missing or blank as unset (Vercel sometimes stores empty strings)."""
    value = os.getenv(name)
    if value is None:
        return default
    value = value.strip()
    return value if value else default


SECRET_KEY = _env("DJANGO_SECRET_KEY", "dev-insecure-change-me")
DEBUG = _env("DJANGO_DEBUG", "true").lower() == "true"
ALLOWED_HOSTS = [
    host.strip()
    for host in _env("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1").split(",")
    if host.strip()
]
# Convenience for Render / similar PaaS when host is passed via env as comma list.
if os.getenv("RENDER_EXTERNAL_HOSTNAME"):
    ALLOWED_HOSTS.append(os.environ["RENDER_EXTERNAL_HOSTNAME"])
# Vercel production / preview hosts
if _env("VERCEL") == "1" or _env("VERCEL_ENV"):
    if ".vercel.app" not in ALLOWED_HOSTS:
        ALLOWED_HOSTS.append(".vercel.app")
    # Deployment-specific hostname (no scheme), e.g. bargain-labs-xxx.vercel.app
    vercel_url = _env("VERCEL_URL")
    if vercel_url:
        ALLOWED_HOSTS.append(vercel_url.split("/")[0])
# Twilio / ngrok webhook host (so voice callbacks are not DisallowedHost)
_twilio_base = _env("TWILIO_WEBHOOK_BASE_URL", "")
if _twilio_base:
    _host = urlparse(_twilio_base).hostname
    if _host and _host not in ALLOWED_HOSTS:
        ALLOWED_HOSTS.append(_host)
# Common ngrok suffixes for local Twilio testing
for _suffix in (".ngrok-free.dev", ".ngrok-free.app", ".ngrok.io"):
    if _suffix not in ALLOWED_HOSTS:
        ALLOWED_HOSTS.append(_suffix)

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


database_url = _env("DATABASE_URL", "")
if database_url:
    try:
        DATABASES = {"default": _database_from_url(database_url)}
    except ValueError:
        # Bad DATABASE_URL should not crash the whole serverless import.
        DATABASES = {
            "default": {
                "ENGINE": "django.db.backends.sqlite3",
                "NAME": BASE_DIR / "db.sqlite3",
            }
        }
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
    for origin in _env("CORS_ALLOWED_ORIGINS", "http://localhost:5173").split(",")
    if origin.strip()
]
CORS_ALLOW_CREDENTIALS = True

SUPABASE_URL = _env("SUPABASE_URL", "")
SUPABASE_JWT_SECRET = _env("SUPABASE_JWT_SECRET", "")
SUPABASE_SERVICE_ROLE_KEY = _env("SUPABASE_SERVICE_ROLE_KEY", "")

SHOPIFY_API_KEY = _env("SHOPIFY_API_KEY", "")
SHOPIFY_API_SECRET = _env("SHOPIFY_API_SECRET", "")
SHOPIFY_SCOPES = _env(
    "SHOPIFY_SCOPES",
    "write_draft_orders,write_inventory,read_inventory,read_locations,"
    "read_orders,write_orders,read_products,write_products",
)
SHOPIFY_API_VERSION = _env("SHOPIFY_API_VERSION", "2024-10")
SHOPIFY_REDIRECT_URI = _env(
    "SHOPIFY_REDIRECT_URI",
    "http://localhost:8000/api/shopify/callback/",
)
# Public HTTPS origin for Shopify webhooks (e.g. https://xxxx.ngrok-free.app).
# Localhost cannot receive webhooks; catalog still auto-refreshes when you open Products.
SHOPIFY_APP_URL = _env("SHOPIFY_APP_URL", "")
FRONTEND_URL = _env("FRONTEND_URL", "http://localhost:5173")

# LangGraph agent (Milestone 2). Local default: http://127.0.0.1:8080
AGENT_SERVICE_URL = _env("AGENT_SERVICE_URL", "")
AGENT_SERVICE_SECRET = _env("AGENT_SERVICE_SECRET", "")

# Twilio Programmable Voice (Milestone 3)
TWILIO_ACCOUNT_SID = _env("TWILIO_ACCOUNT_SID", "")
TWILIO_AUTH_TOKEN = _env("TWILIO_AUTH_TOKEN", "")
TWILIO_FROM_NUMBER = _env("TWILIO_FROM_NUMBER", "")
# Public HTTPS base Twilio can reach (ngrok or deployed API). Not localhost.
TWILIO_WEBHOOK_BASE_URL = _env("TWILIO_WEBHOOK_BASE_URL", "")
TWILIO_WEBHOOK_SECRET = _env("TWILIO_WEBHOOK_SECRET", "")

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "common.auth.SupabaseJWTAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
}

"""Django settings for the test-ecommerce project (module name: shop).

Configuration is driven entirely by environment variables via ``django-environ``.
A missing env file is fine in dev, but ``DEBUG=False`` requires real secrets —
the app refuses to boot if you forget them in production.
"""
from __future__ import annotations

import logging
import sys as _sys
from pathlib import Path

import environ
import sentry_sdk
from sentry_sdk.integrations.django import DjangoIntegration
from sentry_sdk.integrations.logging import LoggingIntegration

BASE_DIR = Path(__file__).resolve().parent.parent

env = environ.Env(
    DJANGO_DEBUG=(bool, True),
    USE_SQLITE=(bool, True),
    EMAIL_USE_TLS=(bool, True),
    STRIPE_TAX_ENABLED=(bool, False),
)
# Load a .env file if present (developer convenience, ignored in CI/prod).
environ.Env.read_env(BASE_DIR / ".env")

DEBUG = env("DJANGO_DEBUG", default=True)

SECRET_KEY = env(
    "DJANGO_SECRET_KEY",
    default="dev-insecure-key-change-me-in-production-please-please-please",
)

ALLOWED_HOSTS = env.list(
    "DJANGO_ALLOWED_HOSTS",
    default=["localhost", "127.0.0.1", "0.0.0.0", "testserver"],
)

# Fail loudly in production if the user forgot to set real secrets.
if not DEBUG:
    if SECRET_KEY.startswith("dev-insecure"):
        raise RuntimeError(
            "DJANGO_DEBUG is False but DJANGO_SECRET_KEY is the dev fallback. "
            "Generate a real secret before deploying."
        )
    if not ALLOWED_HOSTS or ALLOWED_HOSTS == ["*"]:
        raise RuntimeError(
            "DJANGO_ALLOWED_HOSTS must list real hostnames in production."
        )

SITE_ID = 1

INSTALLED_APPS = [
    # Admin theme — must come BEFORE django.contrib.admin.
    "unfold",
    "unfold.contrib.filters",
    "unfold.contrib.forms",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.sites",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.humanize",
    "django.contrib.sitemaps",
    # Auth (django-allauth)
    "allauth",
    "allauth.account",
    "allauth.socialaccount",
    "allauth.socialaccount.providers.google",
    # Local apps
    "core",
    "catalog",
    "cart",
    "payments",
    "accounts",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "csp.middleware.CSPMiddleware",
    "allauth.account.middleware.AccountMiddleware",
    "cart.middleware.CartMergeMiddleware",
]

ROOT_URLCONF = "shop.urls"

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
                "cart.context_processors.cart",
                "core.context_processors.site",
            ],
        },
    },
]

WSGI_APPLICATION = "shop.wsgi.application"
ASGI_APPLICATION = "shop.asgi.application"

# --- Database -------------------------------------------------------------
USE_SQLITE = env("USE_SQLITE", default=True)
if USE_SQLITE:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }
else:
    DATABASES = {
        "default": env.db_url(
            "DATABASE_URL", default="postgres://shop:shop@localhost:5432/shop"
        )
    }
    DATABASES["default"]["CONN_MAX_AGE"] = 600

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

# --- Static / media -------------------------------------------------------
STATIC_URL = "static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"

# Fingerprinted static via WhiteNoise (django>=4.2 storages format). Tests
# and dev fall back to the simpler storage so they don't require collectstatic.
_is_test = "pytest" in " ".join(_sys.argv) or "test" in _sys.argv

STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {
        "BACKEND": (
            "django.contrib.staticfiles.storage.StaticFilesStorage"
            if (DEBUG or _is_test)
            else "whitenoise.storage.CompressedManifestStaticFilesStorage"
        ),
    },
}
WHITENOISE_MAX_AGE = 60 * 60 * 24 * 365  # 1y on fingerprinted assets
WHITENOISE_USE_FINDERS = DEBUG or _is_test  # serve from finders during dev / tests

MEDIA_URL = "media/"
MEDIA_ROOT = BASE_DIR / "media"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# --- Sessions / cart ------------------------------------------------------
SESSION_ENGINE = "django.contrib.sessions.backends.signed_cookies"
SESSION_COOKIE_AGE = 60 * 60 * 24 * 14
CART_SESSION_ID = "cart"

# --- Cache (per-view caching for home + shop) -----------------------------
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "liveboutique-cache",
    }
}

# --- Currency / brand metadata --------------------------------------------
DEFAULT_CURRENCY = env("DEFAULT_CURRENCY", default="USD")
SITE_NAME = "LiveBoutique"
SITE_TAGLINE = "Curated luxury goods"
SITE_BASE_URL = env("SITE_BASE_URL", default="http://localhost:8000")

# --- Stripe ----------------------------------------------------------------
STRIPE_PUBLIC_KEY = env("STRIPE_PUBLIC_KEY", default="pk_test_stub")
STRIPE_SECRET_KEY = env("STRIPE_SECRET_KEY", default="sk_test_stub")
STRIPE_WEBHOOK_SECRET = env("STRIPE_WEBHOOK_SECRET", default="whsec_stub")
STRIPE_TAX_ENABLED = env("STRIPE_TAX_ENABLED", default=False)

# --- Email ----------------------------------------------------------------
EMAIL_BACKEND = env(
    "EMAIL_BACKEND", default="django.core.mail.backends.console.EmailBackend"
)
DEFAULT_FROM_EMAIL = env(
    "DEFAULT_FROM_EMAIL", default="LiveBoutique <noreply@liveboutique.test>"
)
EMAIL_HOST = env("EMAIL_HOST", default="")
EMAIL_PORT = env.int("EMAIL_PORT", default=587)
EMAIL_HOST_USER = env("EMAIL_HOST_USER", default="")
EMAIL_HOST_PASSWORD = env("EMAIL_HOST_PASSWORD", default="")
EMAIL_USE_TLS = env("EMAIL_USE_TLS", default=True)

# --- Seeded admin --------------------------------------------------------
DJANGO_ADMIN_EMAIL = env("DJANGO_ADMIN_EMAIL", default="admin@example.com")
DJANGO_ADMIN_USERNAME = env("DJANGO_ADMIN_USERNAME", default="admin")
DJANGO_ADMIN_PASSWORD = env("DJANGO_ADMIN_PASSWORD", default="ChangeMe123!")

# --- Auth / allauth -------------------------------------------------------
AUTHENTICATION_BACKENDS = [
    "django.contrib.auth.backends.ModelBackend",
    "allauth.account.auth_backends.AuthenticationBackend",
]
LOGIN_REDIRECT_URL = "/account/"
LOGOUT_REDIRECT_URL = "/"
ACCOUNT_LOGIN_METHODS = {"email"}
ACCOUNT_SIGNUP_FIELDS = ["email*", "password1*", "password2*"]
ACCOUNT_EMAIL_VERIFICATION = "optional"
ACCOUNT_UNIQUE_EMAIL = True
ACCOUNT_RATE_LIMITS = {"login_failed": "5/5m"}

GOOGLE_OAUTH_CLIENT_ID = env("GOOGLE_OAUTH_CLIENT_ID", default="")
GOOGLE_OAUTH_CLIENT_SECRET = env("GOOGLE_OAUTH_CLIENT_SECRET", default="")
SOCIALACCOUNT_PROVIDERS = {
    "google": {
        "APP": {
            "client_id": GOOGLE_OAUTH_CLIENT_ID,
            "secret": GOOGLE_OAUTH_CLIENT_SECRET,
            "key": "",
        },
        "SCOPE": ["profile", "email"],
        "AUTH_PARAMS": {"access_type": "online"},
    }
}

# --- Analytics -----------------------------------------------------------
POSTHOG_API_KEY = env("POSTHOG_API_KEY", default="")
POSTHOG_HOST = env("POSTHOG_HOST", default="https://app.posthog.com")

# --- Security headers + CSP ----------------------------------------------
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = "same-origin"
X_FRAME_OPTIONS = "DENY"

if not DEBUG:
    SECURE_SSL_REDIRECT = True
    SECURE_HSTS_SECONDS = 60 * 60 * 24 * 365  # 1y
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True

# Content Security Policy (django-csp 4.x dict format)
_csp_extra: list[str] = []
if POSTHOG_API_KEY:
    _csp_extra.append(POSTHOG_HOST)

CONTENT_SECURITY_POLICY = {
    "DIRECTIVES": {
        "default-src": ["'self'"],
        "script-src": [
            "'self'",
            "'unsafe-inline'",  # required for the inline data-bridge in templates
            "https://js.stripe.com",
            *_csp_extra,
        ],
        "style-src": ["'self'", "'unsafe-inline'", "https://fonts.googleapis.com"],
        "font-src": ["'self'", "https://fonts.gstatic.com", "data:"],
        "img-src": ["'self'", "data:", "blob:", "https:"],
        "connect-src": ["'self'", "https://api.stripe.com", *_csp_extra],
        "frame-src": ["'self'", "https://js.stripe.com", "https://hooks.stripe.com"],
        "form-action": ["'self'"],
        "frame-ancestors": ["'none'"],
        "base-uri": ["'self'"],
    },
}

# --- Logging --------------------------------------------------------------
LOG_LEVEL = env("LOG_LEVEL", default="INFO")
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "json": {
            "()": "shop.logging.JsonFormatter",
        },
        "simple": {
            "format": "%(asctime)s %(levelname)s %(name)s %(message)s",
        },
    },
    "handlers": {
        "stdout": {
            "class": "logging.StreamHandler",
            "stream": "ext://sys.stdout",
            "formatter": "simple" if DEBUG else "json",
        },
    },
    "root": {"handlers": ["stdout"], "level": LOG_LEVEL},
    "loggers": {
        "django": {"handlers": ["stdout"], "level": LOG_LEVEL, "propagate": False},
        "django.server": {
            "handlers": ["stdout"],
            "level": "WARNING",
            "propagate": False,
        },
    },
}

# --- Sentry ---------------------------------------------------------------
SENTRY_DSN = env("SENTRY_DSN", default="")
if SENTRY_DSN:
    sentry_sdk.init(
        dsn=SENTRY_DSN,
        integrations=[
            DjangoIntegration(),
            LoggingIntegration(level=logging.INFO, event_level=logging.ERROR),
        ],
        traces_sample_rate=0.1,
        send_default_pii=False,
        environment="production" if not DEBUG else "development",
    )

# --- pytest ---------------------------------------------------------------
TEST_RUNNER = "django.test.runner.DiscoverRunner"

# --- Unfold admin --------------------------------------------------------
UNFOLD = {
    "SITE_TITLE": "LiveBoutique Admin",
    "SITE_HEADER": "LiveBoutique",
    "SITE_URL": "/",
    "COLORS": {
        "primary": {
            "50": "250 245 235",
            "100": "245 235 215",
            "200": "235 215 175",
            "300": "225 195 135",
            "400": "215 175 95",
            "500": "200 160 80",
            "600": "175 140 65",
            "700": "150 120 50",
            "800": "120 95 40",
            "900": "90 70 30",
            "950": "60 45 20",
        },
    },
}

"""
Base settings shared by every environment.

Secrets and credentials are read from environment variables (or from
backend/.env during local development). Nothing sensitive is hard-coded.
PostgreSQL is the only supported database.
"""
from pathlib import Path

import environ

# backend/ directory
BASE_DIR = Path(__file__).resolve().parent.parent.parent

env = environ.Env()
environ.Env.read_env(BASE_DIR / ".env")

# --- Core -------------------------------------------------------------------

# Required. Django will not start without it.
SECRET_KEY = env("SECRET_KEY")

# Overridden per environment (dev.py / prod.py).
DEBUG = False

ROOT_URLCONF = "config.urls"
WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

# --- Applications -----------------------------------------------------------

DJANGO_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
]

THIRD_PARTY_APPS = [
    "rest_framework",
    "corsheaders",
    "django_filters",
]

# Project apps (each lives in backend/apps/).
LOCAL_APPS = [
    "apps.destinations",
    "apps.packages",
    "apps.bookings",
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    # CorsMiddleware must come before any middleware that can generate
    # responses (CommonMiddleware, WhiteNoise).
    "corsheaders.middleware.CorsMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

# --- Database: PostgreSQL ONLY ----------------------------------------------
# No SQLite and no fallback. A missing variable raises ImproperlyConfigured.

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": env("DB_NAME"),
        "USER": env("DB_USER"),
        "PASSWORD": env("DB_PASSWORD"),
        "HOST": env("DB_HOST", default="localhost"),
        "PORT": env("DB_PORT", default="5432"),
        "CONN_MAX_AGE": env.int("DB_CONN_MAX_AGE", default=60),
        "OPTIONS": {"sslmode": env("DB_SSLMODE", default="prefer")},
    }
}
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# --- Cache (used for API throttling) ------------------------------------------
# A PostgreSQL table, so no extra service is needed. Create it once with:
#   python manage.py createcachetable
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.db.DatabaseCache",
        "LOCATION": "django_cache_table",
    }
}

# --- Authentication (Django admin only) -------------------------------------

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# --- Internationalization ---------------------------------------------------

LANGUAGE_CODE = "en-us"
TIME_ZONE = env("TIME_ZONE", default="Africa/Nairobi")
USE_I18N = True
USE_TZ = True

# --- Static and media files -------------------------------------------------

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

# Images are uploaded through Django admin. Local filesystem storage is used
# for development; production storage is decided later (swap STORAGES).
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
}

# --- Django REST Framework (per api-contract.md) ----------------------------

REST_FRAMEWORK = {
    # Public API: no authentication, no permissions required.
    "DEFAULT_AUTHENTICATION_CLASSES": [],
    "DEFAULT_PERMISSION_CLASSES": ["rest_framework.permissions.AllowAny"],
    # JSON in, JSON out.
    "DEFAULT_RENDERER_CLASSES": ["rest_framework.renderers.JSONRenderer"],
    "DEFAULT_PARSER_CLASSES": ["rest_framework.parsers.JSONParser"],
    "DEFAULT_FILTER_BACKENDS": ["django_filters.rest_framework.DjangoFilterBackend"],
    # {"count", "next", "previous", "results"} with a page size of 12.
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 12,
    # Rate limit for booking submissions (see apps/bookings/throttles.py).
    "DEFAULT_THROTTLE_RATES": {
        "booking_create": env("BOOKING_THROTTLE_RATE", default="5/hour"),
    },
    # Number of reverse proxies in front of Django. 0 means "use the real
    # connection address and ignore X-Forwarded-For", which clients can fake.
    # Behind a proxy in production, set NUM_PROXIES to the number of proxies.
    "NUM_PROXIES": env.int("NUM_PROXIES", default=0),
}

# --- CORS -------------------------------------------------------------------
# The contract allows the frontend origin http://localhost:5173.

CORS_ALLOWED_ORIGINS = env.list(
    "CORS_ALLOWED_ORIGINS", default=["http://localhost:5173"]
)
CORS_URLS_REGEX = r"^/api/.*$"
CORS_ALLOW_METHODS = ["GET", "HEAD", "OPTIONS", "POST"]
CORS_ALLOW_CREDENTIALS = False

# --- Logging ----------------------------------------------------------------

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {"console": {"class": "logging.StreamHandler"}},
    "root": {
        "handlers": ["console"],
        "level": env("LOG_LEVEL", default="INFO"),
    },
}
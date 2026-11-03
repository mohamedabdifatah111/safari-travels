"""
Test settings.

The database is still PostgreSQL (inherited from base.py). Django creates and
destroys a separate "test_<DB_NAME>" database, so your development data is
never touched.
"""
import tempfile
from pathlib import Path

from .base import *  # noqa: F401,F403

DEBUG = False
ALLOWED_HOSTS = ["testserver", "localhost"]

# Faster password hashing in tests only.
PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]

# Uploaded test images go to a temp folder, not backend/media/.
MEDIA_ROOT = Path(tempfile.gettempdir()) / "safari_travels_test_media"

# Throttle counters live in memory during tests (not the database). This is a
# cache only; the database stays PostgreSQL.
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "safari-travels-tests",
    }
}
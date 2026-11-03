"""
Shared helpers for the automated tests (not used by the application itself).
"""
import tempfile
from contextlib import contextmanager
from datetime import timedelta
from decimal import Decimal
from itertools import count

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings
from django.utils import timezone

from apps.bookings.models import Booking
from apps.destinations.models import Destination
from apps.packages.models import TravelPackage

_counter = count(1)


def make_destination(**overrides):
    n = next(_counter)
    data = {
        "name": f"Destination {n}",
        "country": "Kenya",
        "slug": f"destination-{n}",
        "short_description": "Short description.",
        "description": "Full description.",
        "is_active": True,
    }
    data.update(overrides)
    return Destination.objects.create(**data)


def make_package(destination=None, **overrides):
    n = next(_counter)
    data = {
        "destination": destination or make_destination(),
        "title": f"Package {n}",
        "slug": f"package-{n}",
        "price": Decimal("850.00"),
        "currency": "USD",
        "duration_days": 3,
        "short_description": "Short description.",
        "description": "Full description.",
        "includes": "Park fees\nMeals",
        "excludes": "Flights",
        "max_group_size": 8,
        "is_featured": False,
        "is_active": True,
    }
    data.update(overrides)
    return TravelPackage.objects.create(**data)


def future_date(days=30):
    return timezone.localdate() + timedelta(days=days)


def make_booking(package, **overrides):
    data = {
        "package": package,
        "full_name": "Amina Hassan",
        "email": "amina@example.com",
        "phone": "+254700000000",
        "travel_date": future_date(),
        "number_of_travelers": 2,
    }
    data.update(overrides)
    return Booking.objects.create(**data)


def booking_payload(package_obj, **overrides):
    """
    JSON body for POST /api/bookings/ (the example from the contract).

    The first argument is named "package_obj" so that tests can still pass
    package=<id> in overrides to replace the package ID.
    """
    data = {
        "package": package_obj.pk,
        "full_name": "Amina Hassan",
        "email": "amina@example.com",
        "phone": "+254700000000",
        "travel_date": future_date().isoformat(),
        "number_of_travelers": 2,
        "message": "We would like a vegetarian meal option.",
    }
    data.update(overrides)
    return data


def fake_image(name="photo.png"):
    # The model layer does not inspect image bytes, so a placeholder is enough.
    return SimpleUploadedFile(name, b"not-a-real-image", content_type="image/png")


@contextmanager
def temporary_media():
    """Store uploaded files in a throwaway folder, deleted afterwards."""
    with tempfile.TemporaryDirectory() as path, override_settings(MEDIA_ROOT=path):
        yield path
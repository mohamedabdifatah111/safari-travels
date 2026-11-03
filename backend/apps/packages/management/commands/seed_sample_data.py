"""Development helper: create sample destinations and packages."""
from decimal import Decimal

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from apps.destinations.models import Destination
from apps.packages.models import ItineraryDay, TravelPackage


class Command(BaseCommand):
    help = "Create sample destinations and packages for local development."

    def handle(self, *args, **options):
        if not settings.DEBUG:
            raise CommandError("seed_sample_data only runs with DEBUG=True.")

        mara, _ = Destination.objects.update_or_create(
            slug="maasai-mara",
            defaults={
                "name": "Maasai Mara",
                "country": "Kenya",
                "short_description": "Wildlife and the Great Migration.",
                "description": "Kenya's most famous reserve, home to the Big Five.",
                "is_active": True,
            },
        )
        zanzibar, _ = Destination.objects.update_or_create(
            slug="zanzibar",
            defaults={
                "name": "Zanzibar",
                "country": "Tanzania",
                "short_description": "White beaches and Stone Town.",
                "description": "An island of spice markets and turquoise water.",
                "is_active": True,
            },
        )
        closed, _ = Destination.objects.update_or_create(
            slug="closed-destination",
            defaults={
                "name": "Closed Destination",
                "country": "Nowhere",
                "short_description": "Inactive, should be hidden.",
                "description": "Used to test that inactive destinations are hidden.",
                "is_active": False,
            },
        )

        packages = [
            # (slug, destination, title, price, days, max_group, featured, active)
            ("3-day-maasai-mara-safari", mara, "3-Day Maasai Mara Safari", "850.00", 3, 8, True, True),
            ("5-day-mara-migration", mara, "5-Day Mara Migration Experience", "1500.00", 5, 6, False, True),
            ("zanzibar-beach-escape", zanzibar, "Zanzibar Beach Escape", "600.00", 4, 10, True, True),
            ("retired-mara-trip", mara, "Retired Mara Trip (hidden)", "400.00", 2, 4, False, False),
            ("closed-destination-trip", closed, "Closed Destination Trip (hidden)", "300.00", 2, 4, False, True),
        ]
        created = {}
        for slug, dest, title, price, days, group, featured, active in packages:
            created[slug], _ = TravelPackage.objects.update_or_create(
                slug=slug,
                defaults={
                    "destination": dest,
                    "title": title,
                    "price": Decimal(price),
                    "currency": "USD",
                    "duration_days": days,
                    "short_description": f"{title}: short description.",
                    "description": f"{title}: full description.",
                    "includes": "Park fees\nAccommodation\nMeals\nProfessional guide",
                    "excludes": "International flights\nTravel insurance",
                    "max_group_size": group,
                    "is_featured": featured,
                    "is_active": active,
                },
            )

        for day, title in [(1, "Arrival"), (2, "Game drives"), (3, "Departure")]:
            ItineraryDay.objects.update_or_create(
                package=created["3-day-maasai-mara-safari"],
                day=day,
                defaults={"title": title, "description": f"Day {day}: {title}."},
            )

        self.stdout.write(self.style.SUCCESS("Sample data ready."))
        self.stdout.write("Visible packages and their IDs:")
        for pkg in TravelPackage.objects.filter(
            is_active=True, destination__is_active=True
        ):
            self.stdout.write(f"  id={pkg.id}  {pkg.title}  {pkg.price} {pkg.currency}")
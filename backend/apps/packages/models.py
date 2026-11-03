from decimal import Decimal

from django.core.validators import MinValueValidator, RegexValidator
from django.db import models

from apps.destinations.models import Destination


def _split_lines(text):
    """Turn a one-item-per-line text block into a list of non-empty strings."""
    return [line.strip() for line in text.splitlines() if line.strip()]


class TravelPackage(models.Model):
    """A bookable trip. Prices are per person (pending confirmation)."""

    destination = models.ForeignKey(
        Destination,
        on_delete=models.PROTECT,
        related_name="packages",
    )
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=220, unique=True)
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.00"))],
        help_text="Price per person.",
    )
    # PLACEHOLDER: the initial currency is still to be confirmed with the
    # frontend developer. Changing this default later needs a new migration.
    currency = models.CharField(
        max_length=3,
        default="USD",
        validators=[
            RegexValidator(
                r"^[A-Z]{3}$",
                "Use a 3-letter uppercase currency code, such as USD.",
            )
        ],
    )
    duration_days = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1)],
    )
    # Optional: the API returns null when no image has been uploaded.
    image = models.ImageField(upload_to="packages/", blank=True)
    short_description = models.CharField(max_length=300)
    description = models.TextField()
    includes = models.TextField(
        blank=True,
        help_text="What is included. Write one item per line.",
    )
    excludes = models.TextField(
        blank=True,
        help_text="What is not included. Write one item per line.",
    )
    max_group_size = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1)],
    )
    is_featured = models.BooleanField(default=False)
    is_active = models.BooleanField(
        default=True,
        help_text="Untick to hide this package from the website.",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["id"]
        indexes = [
            models.Index(
                fields=["is_active", "is_featured"], name="pkg_active_featured_idx"
            ),
            models.Index(fields=["destination", "is_active"], name="pkg_dest_active_idx"),
            models.Index(fields=["price"], name="pkg_price_idx"),
        ]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(price__gte=0), name="package_price_gte_0"
            ),
            models.CheckConstraint(
                condition=models.Q(duration_days__gte=1),
                name="package_duration_gte_1",
            ),
            models.CheckConstraint(
                condition=models.Q(max_group_size__gte=1),
                name="package_max_group_size_gte_1",
            ),
        ]

    def __str__(self):
        return self.title

    @property
    def includes_list(self):
        return _split_lines(self.includes)

    @property
    def excludes_list(self):
        return _split_lines(self.excludes)


class ItineraryDay(models.Model):
    """One day of a package's itinerary. Staff add these as rows in admin."""

    package = models.ForeignKey(
        TravelPackage,
        on_delete=models.CASCADE,
        related_name="itinerary_days",
    )
    day = models.PositiveSmallIntegerField(validators=[MinValueValidator(1)])
    title = models.CharField(max_length=200)
    description = models.TextField()

    class Meta:
        ordering = ["package", "day"]
        constraints = [
            models.UniqueConstraint(
                fields=["package", "day"], name="unique_itinerary_day_per_package"
            ),
            models.CheckConstraint(
                condition=models.Q(day__gte=1), name="itinerary_day_gte_1"
            ),
        ]

    def __str__(self):
        return f"{self.package} - Day {self.day}: {self.title}"
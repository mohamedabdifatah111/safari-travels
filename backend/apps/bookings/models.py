from decimal import Decimal

from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models

from apps.packages.models import TravelPackage


class Booking(models.Model):
    """
    A customer's booking request.

    A booking request is NOT a confirmed booking and NOT a payment. Staff
    review requests in Django admin and change the status.

    Money fields are calculated here on the server, never taken from the
    client. The package price and currency are copied at creation time, so
    later price changes do not alter historical bookings.
    """

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        CONFIRMED = "confirmed", "Confirmed"
        CANCELLED = "cancelled", "Cancelled"

    package = models.ForeignKey(
        TravelPackage,
        on_delete=models.PROTECT,
        related_name="bookings",
    )
    full_name = models.CharField(max_length=120)
    email = models.EmailField()
    phone = models.CharField(max_length=20)
    travel_date = models.DateField()
    number_of_travelers = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1)],
    )
    message = models.CharField(max_length=1000, blank=True)
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
    )

    # Price snapshot, set automatically in save(). Not editable by anyone.
    unit_price = models.DecimalField(
        max_digits=10, decimal_places=2, editable=False
    )
    currency = models.CharField(max_length=3, editable=False)
    total_price = models.DecimalField(
        max_digits=12, decimal_places=2, editable=False
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(
                fields=["status", "travel_date"], name="booking_status_date_idx"
            ),
            models.Index(fields=["-created_at"], name="booking_created_idx"),
            models.Index(fields=["email"], name="booking_email_idx"),
        ]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(number_of_travelers__gte=1),
                name="booking_travelers_gte_1",
            ),
            models.CheckConstraint(
                condition=models.Q(unit_price__gte=0),
                name="booking_unit_price_gte_0",
            ),
            models.CheckConstraint(
                condition=models.Q(total_price__gte=0),
                name="booking_total_price_gte_0",
            ),
        ]

    def __str__(self):
        return f"Booking #{self.pk or 'new'}: {self.full_name} - {self.package}"

    def clean(self):
        """Enforce the group-size limit when a booking is created."""
        super().clean()
        if (
            self._state.adding
            and self.package_id
            and self.number_of_travelers is not None
            and self.number_of_travelers > self.package.max_group_size
        ):
            raise ValidationError(
                {
                    "number_of_travelers": (
                        "Ensure this value is no greater than the package's "
                        f"maximum group size ({self.package.max_group_size})."
                    )
                }
            )

    def save(self, *args, **kwargs):
        if self._state.adding:
            # Snapshot price and currency, then calculate the total.
            # Pricing is per person (pending confirmation).
            self.unit_price = self.package.price
            self.currency = self.package.currency
            self.total_price = (
                self.unit_price * self.number_of_travelers
            ).quantize(Decimal("0.01"))
        super().save(*args, **kwargs)
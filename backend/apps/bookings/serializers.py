from django.utils import timezone
from rest_framework import serializers

from apps.packages.models import TravelPackage

from .models import Booking


class BookingCreateSerializer(serializers.ModelSerializer):
    """
    Validates and creates a booking request.

    The price snapshot, currency and total are calculated by Booking.save();
    nothing money-related is accepted from the client.
    """

    package = serializers.PrimaryKeyRelatedField(
        queryset=TravelPackage.objects.filter(
            is_active=True,
            destination__is_active=True,
        )
    )

    class Meta:
        model = Booking
        fields = [
            "id",
            "package",
            "full_name",
            "email",
            "phone",
            "travel_date",
            "number_of_travelers",
            "message",
            "status",
            "total_price",
            "created_at",
        ]
        read_only_fields = ["id", "status", "total_price", "created_at"]

    def validate_travel_date(self, value):
        if value <= timezone.localdate():
            raise serializers.ValidationError("Travel date must be in the future.")
        return value

    def validate(self, attrs):
        package = attrs["package"]
        if attrs["number_of_travelers"] > package.max_group_size:
            raise serializers.ValidationError(
                {
                    "number_of_travelers": [
                        "Ensure this value is no greater than the package's "
                        f"maximum group size ({package.max_group_size})."
                    ]
                }
            )
        return attrs
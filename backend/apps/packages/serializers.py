from rest_framework import serializers

from apps.destinations.models import Destination

from .models import ItineraryDay, TravelPackage


class PackageDestinationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Destination
        fields = ["id", "name"]


class ItineraryDaySerializer(serializers.ModelSerializer):
    class Meta:
        model = ItineraryDay
        fields = ["day", "title", "description"]


class PackageListSerializer(serializers.ModelSerializer):
    destination = PackageDestinationSerializer(read_only=True)

    class Meta:
        model = TravelPackage
        fields = [
            "id",
            "title",
            "slug",
            "destination",
            "price",
            "currency",
            "duration_days",
            "image",
            "short_description",
            "is_featured",
        ]


class PackageDetailSerializer(PackageListSerializer):
    # Stored as one-item-per-line text; returned as an array of strings.
    includes = serializers.ListField(
        child=serializers.CharField(), source="includes_list", read_only=True
    )
    excludes = serializers.ListField(
        child=serializers.CharField(), source="excludes_list", read_only=True
    )
    itinerary = ItineraryDaySerializer(
        source="itinerary_days", many=True, read_only=True
    )

    class Meta(PackageListSerializer.Meta):
        fields = PackageListSerializer.Meta.fields + [
            "description",
            "includes",
            "excludes",
            "itinerary",
            "max_group_size",
        ]
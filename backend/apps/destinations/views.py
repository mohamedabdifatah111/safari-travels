from django.db.models import Count, Q
from rest_framework import viewsets

from .models import Destination
from .serializers import DestinationDetailSerializer, DestinationListSerializer


class DestinationViewSet(viewsets.ReadOnlyModelViewSet):
    """Public, read-only access to active destinations."""

    # Detail URLs use integer IDs only (per the API contract).
    lookup_value_regex = r"\d+"

    def get_queryset(self):
        return (
            Destination.objects.filter(is_active=True)
            .annotate(
                package_count=Count(
                    "packages",
                    filter=Q(packages__is_active=True),
                )
            )
            # Explicit ordering: Meta.ordering is ignored for grouped queries.
            .order_by("name", "id")
        )

    def get_serializer_class(self):
        if self.action == "retrieve":
            return DestinationDetailSerializer
        return DestinationListSerializer
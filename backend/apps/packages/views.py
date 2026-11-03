from rest_framework import viewsets

from .filters import PackageFilter
from .models import TravelPackage
from .serializers import PackageDetailSerializer, PackageListSerializer


class PackageViewSet(viewsets.ReadOnlyModelViewSet):
    """Public, read-only access to active packages in active destinations."""

    lookup_value_regex = r"\d+"
    filterset_class = PackageFilter

    def get_queryset(self):
        queryset = TravelPackage.objects.filter(
            is_active=True,
            destination__is_active=True,
        ).select_related("destination")
        if self.action == "retrieve":
            queryset = queryset.prefetch_related("itinerary_days")
        return queryset

    def get_serializer_class(self):
        if self.action == "retrieve":
            return PackageDetailSerializer
        return PackageListSerializer
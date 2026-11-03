from django import forms
from django_filters import rest_framework as filters

from .models import TravelPackage


class IntegerFilter(filters.NumberFilter):
    """Accepts whole numbers only; anything else returns HTTP 400."""

    field_class = forms.IntegerField


class PackageFilter(filters.FilterSet):
    destination = IntegerFilter(field_name="destination_id")
    featured = filters.BooleanFilter(field_name="is_featured")
    min_price = filters.NumberFilter(field_name="price", lookup_expr="gte")
    max_price = filters.NumberFilter(field_name="price", lookup_expr="lte")

    class Meta:
        model = TravelPackage
        fields = []
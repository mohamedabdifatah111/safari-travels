from rest_framework import serializers

from .models import Destination


class DestinationListSerializer(serializers.ModelSerializer):
    # Annotated in the view (active packages only).
    package_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Destination
        fields = [
            "id",
            "name",
            "country",
            "slug",
            "short_description",
            "image",
            "package_count",
        ]


class DestinationDetailSerializer(DestinationListSerializer):
    class Meta(DestinationListSerializer.Meta):
        fields = DestinationListSerializer.Meta.fields + ["description"]
from django import forms
from django.contrib import admin
from django.db import models
from django.utils.html import format_html

from .models import ItineraryDay, TravelPackage


class ItineraryDayInline(admin.TabularInline):
    """Itinerary rows, edited inside the package page."""

    model = ItineraryDay
    extra = 1
    ordering = ("day",)
    fields = ("day", "title", "description")
    formfield_overrides = {
        models.TextField: {"widget": forms.Textarea(attrs={"rows": 3, "cols": 60})},
    }


@admin.register(TravelPackage)
class TravelPackageAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "destination",
        "price_display",
        "duration_days",
        "is_featured",
        "is_active",
        "image_preview",
    )
    list_display_links = ("title",)
    list_editable = ("is_featured", "is_active")
    list_filter = ("is_active", "is_featured", "destination")
    search_fields = ("title", "destination__name", "short_description")
    prepopulated_fields = {"slug": ("title",)}
    readonly_fields = ("image_preview", "created_at", "updated_at")
    list_select_related = ("destination",)
    ordering = ("id",)
    inlines = [ItineraryDayInline]
    formfield_overrides = {
        models.TextField: {"widget": forms.Textarea(attrs={"rows": 6, "cols": 80})},
    }

    fieldsets = (
        (
            None,
            {
                "fields": ("title", "slug", "destination", "is_featured", "is_active"),
            },
        ),
        (
            "Pricing and size",
            {
                "fields": ("price", "currency", "duration_days", "max_group_size"),
                "description": (
                    "The price is per person. The booking total is calculated "
                    "automatically as price x number of travelers. Changing the "
                    "price here does not change existing bookings."
                ),
            },
        ),
        (
            "Descriptions",
            {
                "fields": ("short_description", "description"),
            },
        ),
        (
            "What is included",
            {
                "fields": ("includes", "excludes"),
                "description": "Write one item per line.",
            },
        ),
        (
            "Image",
            {
                "fields": ("image", "image_preview"),
            },
        ),
        (
            "Record information",
            {
                "fields": ("created_at", "updated_at"),
                "classes": ("collapse",),
            },
        ),
    )

    @admin.display(description="Price (per person)", ordering="price")
    def price_display(self, obj):
        return f"{obj.price} {obj.currency}"

    @admin.display(description="Image")
    def image_preview(self, obj):
        if not obj or not obj.image:
            return "No image"
        return format_html(
            '<img src="{}" style="max-height: 60px; border-radius: 4px;" alt="">',
            obj.image.url,
        )
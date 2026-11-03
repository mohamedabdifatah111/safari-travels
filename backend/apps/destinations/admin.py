from django.contrib import admin
from django.utils.html import format_html

from .models import Destination


@admin.register(Destination)
class DestinationAdmin(admin.ModelAdmin):
    list_display = ("name", "country", "image_preview", "is_active", "updated_at")
    list_display_links = ("name",)
    list_editable = ("is_active",)
    list_filter = ("is_active", "country")
    search_fields = ("name", "country", "short_description")
    prepopulated_fields = {"slug": ("name",)}
    readonly_fields = ("image_preview", "created_at", "updated_at")
    ordering = ("name",)

    fieldsets = (
        (
            None,
            {
                "fields": ("name", "country", "slug", "is_active"),
            },
        ),
        (
            "Descriptions",
            {
                "fields": ("short_description", "description"),
            },
        ),
        (
            "Image",
            {
                "fields": ("image", "image_preview"),
                "description": "Upload a photo. The website shows it on the destination.",
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

    @admin.display(description="Image")
    def image_preview(self, obj):
        if not obj or not obj.image:
            return "No image"
        return format_html(
            '<img src="{}" style="max-height: 60px; border-radius: 4px;" alt="">',
            obj.image.url,
        )
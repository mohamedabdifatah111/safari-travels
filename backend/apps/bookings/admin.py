from django.contrib import admin
from django.utils import timezone

from .models import Booking


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    """
    Staff view of booking requests.

    Only the status can be changed. Everything the customer submitted, and the
    price snapshot calculated by the server, is read-only. Bookings are created
    by the public API (which validates them), so adding is disabled here.
    """

    list_display = (
        "id",
        "full_name",
        "email",
        "package",
        "travel_date",
        "number_of_travelers",
        "total_display",
        "status",
        "created_at",
    )
    list_display_links = ("id", "full_name")
    list_filter = ("status", "travel_date", "package")
    search_fields = ("full_name", "email", "phone")
    date_hierarchy = "travel_date"
    list_select_related = ("package",)
    ordering = ("-created_at",)
    actions = ["mark_confirmed", "mark_cancelled", "mark_pending"]

    # Everything except "status" is read-only.
    readonly_fields = (
        "full_name",
        "email",
        "phone",
        "package",
        "travel_date",
        "number_of_travelers",
        "message",
        "unit_price",
        "currency",
        "total_price",
        "created_at",
        "updated_at",
    )

    fieldsets = (
        (
            "Status",
            {
                "fields": ("status",),
                "description": (
                    "A booking request is not a confirmed booking or a payment. "
                    "Change the status once you have contacted the customer."
                ),
            },
        ),
        ("Customer", {"fields": ("full_name", "email", "phone")}),
        (
            "Trip",
            {
                "fields": (
                    "package",
                    "travel_date",
                    "number_of_travelers",
                    "message",
                )
            },
        ),
        (
            "Price (calculated by the system)",
            {"fields": ("unit_price", "currency", "total_price")},
        ),
        (
            "Record information",
            {"fields": ("created_at", "updated_at"), "classes": ("collapse",)},
        ),
    )

    @admin.display(description="Total", ordering="total_price")
    def total_display(self, obj):
        return f"{obj.total_price} {obj.currency}"

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        # Only superusers may delete booking records.
        return request.user.is_superuser

    def _set_status(self, request, queryset, status, label):
        # update() skips save(), so refresh updated_at ourselves.
        count = queryset.update(status=status, updated_at=timezone.now())
        self.message_user(request, f"{count} booking(s) marked as {label}.")

    # permissions=["change"]: only staff who may change bookings can run these.
    @admin.action(
        description="Mark selected bookings as confirmed", permissions=["change"]
    )
    def mark_confirmed(self, request, queryset):
        self._set_status(request, queryset, Booking.Status.CONFIRMED, "confirmed")

    @admin.action(
        description="Mark selected bookings as cancelled", permissions=["change"]
    )
    def mark_cancelled(self, request, queryset):
        self._set_status(request, queryset, Booking.Status.CANCELLED, "cancelled")

    @admin.action(
        description="Mark selected bookings as pending", permissions=["change"]
    )
    def mark_pending(self, request, queryset):
        self._set_status(request, queryset, Booking.Status.PENDING, "pending")
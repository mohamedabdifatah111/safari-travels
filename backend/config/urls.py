"""
Root URL configuration.

Public API routes live under /api/ (see docs/api-contract.md).
"""
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from rest_framework.routers import SimpleRouter

from apps.bookings.views import BookingCreateView
from apps.destinations.views import DestinationViewSet
from apps.packages.views import PackageViewSet

# SimpleRouter (not DefaultRouter) so no extra API-root endpoint is exposed.
router = SimpleRouter()
router.register("destinations", DestinationViewSet, basename="destination")
router.register("packages", PackageViewSet, basename="package")

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/bookings/", BookingCreateView.as_view(), name="booking-create"),
    path("api/", include(router.urls)),
]

# JSON errors for /api/ when DEBUG is False.
handler404 = "config.views.not_found"
handler500 = "config.views.server_error"

# Serve uploaded media only in development.
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
from rest_framework import generics

from .models import Booking
from .serializers import BookingCreateSerializer
from .throttles import BookingRateThrottle


class BookingCreateView(generics.CreateAPIView):
    """
    Public endpoint for submitting a booking request (POST only).

    There is deliberately no list or detail view: booking records are private
    and managed by staff in Django admin. Submissions are rate-limited.
    """

    queryset = Booking.objects.none()
    serializer_class = BookingCreateSerializer
    throttle_classes = [BookingRateThrottle]
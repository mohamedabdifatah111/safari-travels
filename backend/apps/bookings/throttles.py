from rest_framework.throttling import SimpleRateThrottle


class BookingRateThrottle(SimpleRateThrottle):
    """
    Limits booking submissions per client IP address.

    The rate comes from REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"]["booking_create"]
    (setting BOOKING_THROTTLE_RATE, default "5/hour"). Only POST requests are
    counted, and invalid submissions count too, to discourage probing.
    """

    scope = "booking_create"

    def get_cache_key(self, request, view):
        if request.method != "POST":
            return None  # not throttled
        return self.cache_format % {
            "scope": self.scope,
            "ident": self.get_ident(request),
        }
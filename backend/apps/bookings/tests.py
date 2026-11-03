from decimal import Decimal

from django.core.cache import cache
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.db.models import ProtectedError
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APIClient

from apps.factories import (
    booking_payload,
    future_date,
    make_booking,
    make_destination,
    make_package,
)

from .models import Booking
from .serializers import BookingCreateSerializer
from .throttles import BookingRateThrottle

RESPONSE_FIELDS = {
    "id",
    "package",
    "full_name",
    "email",
    "phone",
    "travel_date",
    "number_of_travelers",
    "message",
    "status",
    "total_price",
    "created_at",
}


class BookingModelTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.package = make_package(price=Decimal("850.00"), currency="USD", max_group_size=8)

    def test_status_defaults_to_pending(self):
        self.assertEqual(make_booking(self.package).status, Booking.Status.PENDING)

    def test_save_snapshots_price_and_calculates_total(self):
        booking = make_booking(self.package, number_of_travelers=2)
        self.assertEqual(booking.unit_price, Decimal("850.00"))
        self.assertEqual(booking.currency, "USD")
        self.assertEqual(booking.total_price, Decimal("1700.00"))

    def test_total_is_rounded_to_two_decimals(self):
        package = make_package(price=Decimal("33.33"))
        booking = make_booking(package, number_of_travelers=3)
        self.assertEqual(booking.total_price, Decimal("99.99"))

    def test_currency_comes_from_the_package(self):
        package = make_package(currency="KES")
        self.assertEqual(make_booking(package).currency, "KES")

    def test_later_price_changes_do_not_alter_the_booking(self):
        booking = make_booking(self.package, number_of_travelers=2)
        self.package.price = Decimal("999.00")
        self.package.currency = "EUR"
        self.package.save()

        booking.refresh_from_db()
        self.assertEqual(booking.unit_price, Decimal("850.00"))
        self.assertEqual(booking.total_price, Decimal("1700.00"))
        self.assertEqual(booking.currency, "USD")

        # Editing the booking later (e.g. status) must not recalculate either.
        booking.status = Booking.Status.CONFIRMED
        booking.save()
        booking.refresh_from_db()
        self.assertEqual(booking.total_price, Decimal("1700.00"))

        # Restore the shared fixture for the other tests in this class.
        self.package.price = Decimal("850.00")
        self.package.currency = "USD"
        self.package.save()

    def test_zero_travelers_is_rejected_by_the_database(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            make_booking(self.package, number_of_travelers=0)

    def test_clean_rejects_too_many_travelers_for_a_new_booking(self):
        booking = Booking(
            package=self.package,
            full_name="A",
            email="a@example.com",
            phone="1",
            travel_date=future_date(),
            number_of_travelers=self.package.max_group_size + 1,
        )
        with self.assertRaises(ValidationError) as ctx:
            booking.clean()
        self.assertIn("number_of_travelers", ctx.exception.message_dict)

    def test_clean_accepts_the_maximum_group_size(self):
        booking = Booking(
            package=self.package,
            full_name="A",
            email="a@example.com",
            phone="1",
            travel_date=future_date(),
            number_of_travelers=self.package.max_group_size,
        )
        booking.clean()  # no error

    def test_limit_is_not_enforced_again_on_existing_bookings(self):
        package = make_package(max_group_size=8)
        booking = make_booking(package, number_of_travelers=5)
        package.max_group_size = 2
        package.save()
        booking = Booking.objects.get(pk=booking.pk)
        booking.clean()  # staff can still change the status

    def test_bookings_are_ordered_newest_first(self):
        first = make_booking(self.package)
        second = make_booking(self.package)
        self.assertEqual(list(Booking.objects.all()), [second, first])

    def test_package_with_bookings_cannot_be_deleted(self):
        package = make_package()
        make_booking(package)
        with self.assertRaises(ProtectedError):
            package.delete()

    def test_package_bookings_relationship(self):
        package = make_package()
        make_booking(package)
        make_booking(package)
        self.assertEqual(package.bookings.count(), 2)

    def test_str_mentions_the_customer(self):
        booking = make_booking(self.package, full_name="Amina Hassan")
        self.assertIn("Amina Hassan", str(booking))


class BookingSerializerTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.package = make_package(max_group_size=8)

    def serializer(self, **overrides):
        return BookingCreateSerializer(data=booking_payload(self.package, **overrides))

    def test_valid_payload_is_accepted(self):
        serializer = self.serializer()
        self.assertTrue(serializer.is_valid(), serializer.errors)

    def test_required_fields(self):
        serializer = BookingCreateSerializer(data={})
        self.assertFalse(serializer.is_valid())
        self.assertEqual(
            set(serializer.errors),
            {
                "package",
                "full_name",
                "email",
                "phone",
                "travel_date",
                "number_of_travelers",
            },
        )

    def test_message_is_optional_and_may_be_blank(self):
        payload = booking_payload(self.package)
        del payload["message"]
        self.assertTrue(BookingCreateSerializer(data=payload).is_valid())
        self.assertTrue(self.serializer(message="").is_valid())

    def test_invalid_email(self):
        serializer = self.serializer(email="not-an-email")
        self.assertFalse(serializer.is_valid())
        self.assertEqual(serializer.errors["email"], ["Enter a valid email address."])

    def test_full_name_max_length_is_120(self):
        self.assertTrue(self.serializer(full_name="a" * 120).is_valid())
        serializer = self.serializer(full_name="a" * 121)
        self.assertFalse(serializer.is_valid())
        self.assertIn("full_name", serializer.errors)

    def test_phone_max_length_is_20(self):
        self.assertTrue(self.serializer(phone="1" * 20).is_valid())
        serializer = self.serializer(phone="1" * 21)
        self.assertFalse(serializer.is_valid())
        self.assertIn("phone", serializer.errors)

    def test_message_max_length_is_1000(self):
        self.assertTrue(self.serializer(message="m" * 1000).is_valid())
        serializer = self.serializer(message="m" * 1001)
        self.assertFalse(serializer.is_valid())
        self.assertIn("message", serializer.errors)

    def test_past_date_is_rejected(self):
        serializer = self.serializer(travel_date="2020-01-01")
        self.assertFalse(serializer.is_valid())
        self.assertEqual(
            serializer.errors["travel_date"], ["Travel date must be in the future."]
        )

    def test_today_is_rejected_and_tomorrow_is_accepted(self):
        today = timezone.localdate().isoformat()
        self.assertFalse(self.serializer(travel_date=today).is_valid())
        self.assertTrue(self.serializer(travel_date=future_date(1).isoformat()).is_valid())

    def test_malformed_date_is_rejected(self):
        serializer = self.serializer(travel_date="not-a-date")
        self.assertFalse(serializer.is_valid())
        self.assertIn("travel_date", serializer.errors)

    def test_traveler_count_must_be_at_least_one(self):
        for value in (0, -1):
            serializer = self.serializer(number_of_travelers=value)
            self.assertFalse(serializer.is_valid(), value)
            self.assertIn("number_of_travelers", serializer.errors)

    def test_traveler_count_cannot_exceed_group_size(self):
        too_many = self.package.max_group_size + 1
        serializer = self.serializer(number_of_travelers=too_many)
        self.assertFalse(serializer.is_valid())
        self.assertIn("number_of_travelers", serializer.errors)
        self.assertIn(str(self.package.max_group_size), serializer.errors["number_of_travelers"][0])

    def test_traveler_count_equal_to_group_size_is_accepted(self):
        serializer = self.serializer(number_of_travelers=self.package.max_group_size)
        self.assertTrue(serializer.is_valid(), serializer.errors)

    def test_inactive_package_is_rejected(self):
        package = make_package(is_active=False)
        serializer = BookingCreateSerializer(data=booking_payload(package))
        self.assertFalse(serializer.is_valid())
        self.assertIn("package", serializer.errors)

    def test_package_in_inactive_destination_is_rejected(self):
        package = make_package(destination=make_destination(is_active=False))
        serializer = BookingCreateSerializer(data=booking_payload(package))
        self.assertFalse(serializer.is_valid())
        self.assertIn("package", serializer.errors)

    def test_unknown_package_is_rejected(self):
        serializer = self.serializer(package=999999)
        self.assertFalse(serializer.is_valid())
        self.assertIn("package", serializer.errors)

    def test_client_cannot_set_server_controlled_fields(self):
        serializer = self.serializer(
            status="confirmed", total_price="1.00", id=999, created_at="2020-01-01T00:00:00Z"
        )
        self.assertTrue(serializer.is_valid(), serializer.errors)
        for name in ("status", "total_price", "id", "created_at"):
            self.assertNotIn(name, serializer.validated_data)


class BookingApiTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.package = make_package(price=Decimal("850.00"), currency="USD", max_group_size=8)

    def setUp(self):
        cache.clear()
        self.client = APIClient()
        self.url = reverse("booking-create")

    def post(self, **overrides):
        return self.client.post(
            self.url, booking_payload(self.package, **overrides), format="json"
        )

    def test_successful_booking_returns_201_with_contract_fields(self):
        response = self.post()
        self.assertEqual(response.status_code, 201)
        data = response.json()
        self.assertEqual(set(data), RESPONSE_FIELDS)
        self.assertEqual(data["package"], self.package.pk)
        self.assertEqual(data["full_name"], "Amina Hassan")
        self.assertEqual(data["status"], "pending")
        self.assertEqual(data["total_price"], "1700.00")

    def test_booking_is_saved_with_a_price_snapshot(self):
        self.post()
        booking = Booking.objects.get()
        self.assertEqual(booking.status, Booking.Status.PENDING)
        self.assertEqual(booking.unit_price, Decimal("850.00"))
        self.assertEqual(booking.total_price, Decimal("1700.00"))
        self.assertEqual(booking.currency, "USD")

    def test_booking_works_without_authentication(self):
        self.assertEqual(self.post().status_code, 201)

    def test_server_controlled_values_cannot_be_forged(self):
        response = self.post(
            status="confirmed",
            total_price="1.00",
            unit_price="1.00",
            currency="KES",
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json()["status"], "pending")
        self.assertEqual(response.json()["total_price"], "1700.00")
        booking = Booking.objects.get()
        self.assertEqual(booking.unit_price, Decimal("850.00"))
        self.assertEqual(booking.currency, "USD")

    def test_invalid_email_returns_the_contract_error_format(self):
        response = self.post(email="not-an-email")
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json(), {"email": ["Enter a valid email address."]})
        self.assertEqual(Booking.objects.count(), 0)

    def test_past_date_returns_400(self):
        response = self.post(travel_date="2020-01-01")
        self.assertEqual(response.status_code, 400)
        self.assertIn("travel_date", response.json())
        self.assertEqual(Booking.objects.count(), 0)

    def test_too_many_travelers_returns_400(self):
        response = self.post(number_of_travelers=99)
        self.assertEqual(response.status_code, 400)
        self.assertIn("number_of_travelers", response.json())
        self.assertEqual(Booking.objects.count(), 0)

    def test_zero_travelers_returns_400(self):
        self.assertEqual(self.post(number_of_travelers=0).status_code, 400)

    def test_missing_fields_return_400_with_required_messages(self):
        response = self.client.post(self.url, {}, format="json")
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["full_name"], ["This field is required."])

    def test_inactive_package_returns_400(self):
        package = make_package(is_active=False)
        response = self.client.post(self.url, booking_payload(package), format="json")
        self.assertEqual(response.status_code, 400)
        self.assertIn("package", response.json())

    def test_unknown_package_returns_400(self):
        response = self.post(package=999999)
        self.assertEqual(response.status_code, 400)
        self.assertIn("package", response.json())

    def test_non_object_body_uses_non_field_errors(self):
        response = self.client.post(self.url, data="[]", content_type="application/json")
        self.assertEqual(response.status_code, 400)
        self.assertIn("non_field_errors", response.json())

    def test_bookings_are_not_publicly_readable(self):
        booking = make_booking(self.package)
        self.assertEqual(self.client.get(self.url).status_code, 405)
        self.assertEqual(self.client.get(f"{self.url}{booking.pk}/").status_code, 404)

    def test_other_methods_are_not_allowed(self):
        for method in ("put", "patch", "delete"):
            response = getattr(self.client, method)(self.url, {}, format="json")
            self.assertEqual(response.status_code, 405, method.upper())


class BookingThrottleTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.package = make_package()
        rate = BookingRateThrottle.THROTTLE_RATES["booking_create"]
        cls.limit = int(rate.split("/")[0])

    def setUp(self):
        cache.clear()
        self.client = APIClient()
        self.url = reverse("booking-create")

    def tearDown(self):
        cache.clear()

    def send_invalid(self, **extra):
        # An empty body is rejected with 400, but it still counts toward the limit.
        return self.client.post(self.url, {}, format="json", **extra)

    def test_requests_over_the_limit_get_429(self):
        for _ in range(self.limit):
            self.assertEqual(self.send_invalid().status_code, 400)
        response = self.send_invalid()
        self.assertEqual(response.status_code, 429)
        self.assertIn("Retry-After", response)

    def test_valid_bookings_are_throttled_too(self):
        payload = booking_payload(self.package)
        for _ in range(self.limit):
            self.assertEqual(
                self.client.post(self.url, payload, format="json").status_code, 201
            )
        self.assertEqual(
            self.client.post(self.url, payload, format="json").status_code, 429
        )

    def test_each_ip_address_has_its_own_limit(self):
        for _ in range(self.limit):
            self.send_invalid(REMOTE_ADDR="10.0.0.1")
        self.assertEqual(self.send_invalid(REMOTE_ADDR="10.0.0.1").status_code, 429)
        self.assertEqual(self.send_invalid(REMOTE_ADDR="10.0.0.2").status_code, 400)

    def test_fake_forwarded_header_does_not_bypass_the_limit(self):
        for i in range(self.limit):
            self.send_invalid(
                REMOTE_ADDR="10.0.0.3", HTTP_X_FORWARDED_FOR=f"203.0.113.{i}"
            )
        response = self.send_invalid(
            REMOTE_ADDR="10.0.0.3", HTTP_X_FORWARDED_FOR="198.51.100.99"
        )
        self.assertEqual(response.status_code, 429)

    def test_get_requests_do_not_use_up_the_limit(self):
        for _ in range(self.limit + 5):
            self.assertEqual(self.client.get(self.url).status_code, 405)
        response = self.client.post(
            self.url, booking_payload(self.package), format="json"
        )
        self.assertEqual(response.status_code, 201)
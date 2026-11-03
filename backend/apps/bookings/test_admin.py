from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.test import TestCase
from django.urls import reverse

from apps.bookings.models import Booking
from apps.factories import make_booking, make_destination, make_package

User = get_user_model()


def grant(user, *codenames):
    user.user_permissions.add(*Permission.objects.filter(codename__in=codenames))


class AdminAccessTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.destination = make_destination()
        cls.package = make_package(cls.destination)
        cls.booking = make_booking(cls.package)

        cls.superuser = User.objects.create_superuser("boss", "boss@example.com", "pw")
        cls.plain_user = User.objects.create_user("visitor", password="pw")
        cls.staff_no_perms = User.objects.create_user("staff0", password="pw", is_staff=True)
        cls.staff_viewer = User.objects.create_user("viewer", password="pw", is_staff=True)
        grant(cls.staff_viewer, "view_booking")
        cls.staff_editor = User.objects.create_user("editor", password="pw", is_staff=True)
        grant(cls.staff_editor, "view_booking", "change_booking")
        cls.staff_deleter = User.objects.create_user("deleter", password="pw", is_staff=True)
        grant(cls.staff_deleter, "view_booking", "delete_booking")

        cls.changelist = reverse("admin:bookings_booking_changelist")
        cls.change_url = reverse("admin:bookings_booking_change", args=[cls.booking.pk])
        cls.add_url = reverse("admin:bookings_booking_add")
        cls.delete_url = reverse("admin:bookings_booking_delete", args=[cls.booking.pk])

    def admin_urls(self):
        return [
            reverse("admin:index"),
            self.changelist,
            reverse("admin:destinations_destination_changelist"),
            reverse("admin:packages_travelpackage_changelist"),
        ]

    # --- who can get in ----------------------------------------------------

    def test_anonymous_users_are_sent_to_the_login_page(self):
        for url in self.admin_urls():
            response = self.client.get(url)
            self.assertEqual(response.status_code, 302, url)
            self.assertTrue(response.url.startswith(reverse("admin:login")), url)

    def test_logged_in_non_staff_users_are_sent_to_the_login_page(self):
        self.client.force_login(self.plain_user)
        for url in self.admin_urls():
            response = self.client.get(url)
            self.assertEqual(response.status_code, 302, url)
            self.assertTrue(response.url.startswith(reverse("admin:login")), url)

    def test_staff_without_permissions_cannot_open_bookings(self):
        self.client.force_login(self.staff_no_perms)
        self.assertEqual(self.client.get(self.changelist).status_code, 403)
        self.assertEqual(self.client.get(self.change_url).status_code, 403)

    # --- what view-only staff can do ----------------------------------------

    def test_view_only_staff_can_see_bookings(self):
        self.client.force_login(self.staff_viewer)
        self.assertContains(self.client.get(self.changelist), "Amina Hassan")
        self.assertEqual(self.client.get(self.change_url).status_code, 200)

    def test_view_only_staff_cannot_change_a_booking(self):
        self.client.force_login(self.staff_viewer)
        response = self.client.post(self.change_url, {"status": "confirmed"})
        self.assertEqual(response.status_code, 403)
        self.booking.refresh_from_db()
        self.assertEqual(self.booking.status, Booking.Status.PENDING)

    def test_view_only_staff_cannot_run_bulk_actions(self):
        self.client.force_login(self.staff_viewer)
        self.client.post(
            self.changelist,
            {"action": "mark_confirmed", "index": 0, "_selected_action": [self.booking.pk]},
        )
        self.booking.refresh_from_db()
        self.assertEqual(self.booking.status, Booking.Status.PENDING)

    # --- what editors can do -----------------------------------------------

    def test_editor_can_change_the_status(self):
        self.client.force_login(self.staff_editor)
        response = self.client.post(self.change_url, {"status": "confirmed"})
        self.assertEqual(response.status_code, 302)
        self.booking.refresh_from_db()
        self.assertEqual(self.booking.status, Booking.Status.CONFIRMED)

    def test_other_fields_are_read_only_even_if_submitted(self):
        self.client.force_login(self.staff_editor)
        self.client.post(
            self.change_url,
            {
                "status": "confirmed",
                "full_name": "Hacker",
                "total_price": "1.00",
                "number_of_travelers": 50,
            },
        )
        self.booking.refresh_from_db()
        self.assertEqual(self.booking.full_name, "Amina Hassan")
        self.assertEqual(self.booking.total_price, 2 * self.package.price)
        self.assertEqual(self.booking.number_of_travelers, 2)

    def test_editor_can_use_bulk_actions(self):
        self.client.force_login(self.staff_editor)
        for action, expected in (
            ("mark_confirmed", Booking.Status.CONFIRMED),
            ("mark_cancelled", Booking.Status.CANCELLED),
            ("mark_pending", Booking.Status.PENDING),
        ):
            response = self.client.post(
                self.changelist,
                {"action": action, "index": 0, "_selected_action": [self.booking.pk]},
            )
            self.assertEqual(response.status_code, 302, action)
            self.booking.refresh_from_db()
            self.assertEqual(self.booking.status, expected, action)

    # --- adding and deleting ------------------------------------------------

    def test_nobody_can_add_bookings_in_admin(self):
        for user in (self.superuser, self.staff_editor):
            self.client.force_login(user)
            self.assertEqual(self.client.get(self.add_url).status_code, 403)

    def test_staff_cannot_delete_even_with_the_delete_permission(self):
        self.client.force_login(self.staff_deleter)
        self.assertEqual(self.client.get(self.delete_url).status_code, 403)
        self.assertTrue(Booking.objects.filter(pk=self.booking.pk).exists())

    def test_superuser_can_delete_a_booking(self):
        self.client.force_login(self.superuser)
        response = self.client.post(self.delete_url, {"post": "yes"})
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Booking.objects.filter(pk=self.booking.pk).exists())

    # --- search and filters ---------------------------------------------------

    def test_search_by_email_and_name(self):
        self.client.force_login(self.superuser)
        self.assertContains(self.client.get(self.changelist, {"q": "amina@example.com"}), "Amina Hassan")
        self.assertContains(self.client.get(self.changelist, {"q": "Amina"}), "Amina Hassan")
        self.assertNotContains(self.client.get(self.changelist, {"q": "nobody-here"}), "Amina Hassan")

    def test_filter_by_status(self):
        self.client.force_login(self.superuser)
        self.assertContains(self.client.get(self.changelist, {"status__exact": "pending"}), "Amina Hassan")
        self.assertNotContains(self.client.get(self.changelist, {"status__exact": "confirmed"}), "Amina Hassan")


class AdminPagesRenderTests(TestCase):
    """The destination and package admin pages load without errors."""

    @classmethod
    def setUpTestData(cls):
        cls.superuser = User.objects.create_superuser("boss", "boss@example.com", "pw")
        cls.destination = make_destination()
        cls.package = make_package(cls.destination)

    def setUp(self):
        self.client.force_login(self.superuser)

    def test_destination_pages(self):
        for url in (
            reverse("admin:destinations_destination_changelist"),
            reverse("admin:destinations_destination_add"),
            reverse("admin:destinations_destination_change", args=[self.destination.pk]),
        ):
            self.assertEqual(self.client.get(url).status_code, 200, url)

    def test_package_pages_including_the_itinerary_inline(self):
        for url in (
            reverse("admin:packages_travelpackage_changelist"),
            reverse("admin:packages_travelpackage_add"),
            reverse("admin:packages_travelpackage_change", args=[self.package.pk]),
        ):
            self.assertEqual(self.client.get(url).status_code, 200, url)
        self.assertContains(
            self.client.get(
                reverse("admin:packages_travelpackage_change", args=[self.package.pk])
            ),
            "itinerary_days",
        )

    def test_search_and_filters_work(self):
        url = reverse("admin:packages_travelpackage_changelist")
        for params in ({"q": "Package"}, {"is_active__exact": "1"}, {"is_featured__exact": "0"}):
            self.assertEqual(self.client.get(url, params).status_code, 200, params)
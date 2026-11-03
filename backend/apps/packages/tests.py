from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient

from apps.factories import fake_image, make_destination, make_package, temporary_media

from .models import ItineraryDay, TravelPackage
from .serializers import PackageDetailSerializer

LIST_FIELDS = {
    "id",
    "title",
    "slug",
    "destination",
    "price",
    "currency",
    "duration_days",
    "image",
    "short_description",
    "is_featured",
}
DETAIL_FIELDS = LIST_FIELDS | {
    "description",
    "includes",
    "excludes",
    "itinerary",
    "max_group_size",
}


def result_ids(response):
    return {item["id"] for item in response.json()["results"]}


class PackageModelTests(TestCase):
    def test_str_is_the_title(self):
        package = make_package(title="3-Day Safari")
        self.assertEqual(str(package), "3-Day Safari")

    def test_defaults(self):
        package = TravelPackage.objects.create(
            destination=make_destination(),
            title="Defaults",
            slug="defaults",
            price=Decimal("100.00"),
            duration_days=2,
            short_description="s",
            description="d",
            max_group_size=4,
        )
        self.assertEqual(package.currency, "USD")
        self.assertFalse(package.is_featured)
        self.assertTrue(package.is_active)

    def test_slug_must_be_unique(self):
        make_package(slug="same-slug")
        with self.assertRaises(IntegrityError), transaction.atomic():
            make_package(slug="same-slug")

    def test_negative_price_is_rejected_by_the_database(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            make_package(price=Decimal("-1.00"))

    def test_zero_duration_is_rejected_by_the_database(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            make_package(duration_days=0)

    def test_zero_group_size_is_rejected_by_the_database(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            make_package(max_group_size=0)

    def test_currency_must_be_three_uppercase_letters(self):
        package = make_package()
        package.currency = "usd"
        with self.assertRaises(ValidationError) as ctx:
            package.full_clean()
        self.assertIn("currency", ctx.exception.message_dict)

        package.currency = "KES"
        package.full_clean()  # no error

    def test_includes_and_excludes_lists_split_on_lines(self):
        package = make_package(
            includes="  Park fees \n\n Meals\n   \n", excludes=""
        )
        self.assertEqual(package.includes_list, ["Park fees", "Meals"])
        self.assertEqual(package.excludes_list, [])

    def test_itinerary_days_are_ordered_by_day(self):
        package = make_package()
        ItineraryDay.objects.create(package=package, day=2, title="Two", description="d")
        ItineraryDay.objects.create(package=package, day=1, title="One", description="d")
        days = list(package.itinerary_days.values_list("day", flat=True))
        self.assertEqual(days, [1, 2])

    def test_itinerary_day_number_is_unique_per_package(self):
        package = make_package()
        ItineraryDay.objects.create(package=package, day=1, title="One", description="d")
        with self.assertRaises(IntegrityError), transaction.atomic():
            ItineraryDay.objects.create(
                package=package, day=1, title="Again", description="d"
            )

    def test_same_day_number_is_allowed_on_different_packages(self):
        ItineraryDay.objects.create(package=make_package(), day=1, title="A", description="d")
        ItineraryDay.objects.create(package=make_package(), day=1, title="B", description="d")
        self.assertEqual(ItineraryDay.objects.count(), 2)

    def test_deleting_a_package_deletes_its_itinerary(self):
        package = make_package()
        ItineraryDay.objects.create(package=package, day=1, title="One", description="d")
        package.delete()
        self.assertEqual(ItineraryDay.objects.count(), 0)


class PackageSerializerTests(TestCase):
    def test_detail_serializer_returns_lists_and_itinerary(self):
        package = make_package(includes="Park fees\nMeals", excludes="Flights")
        ItineraryDay.objects.create(
            package=package, day=1, title="Arrival", description="Welcome."
        )
        data = PackageDetailSerializer(package).data
        self.assertEqual(data["includes"], ["Park fees", "Meals"])
        self.assertEqual(data["excludes"], ["Flights"])
        self.assertEqual(
            [dict(day) for day in data["itinerary"]],
            [{"day": 1, "title": "Arrival", "description": "Welcome."}],
        )


class PackageListApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.url = reverse("package-list")

    def test_list_returns_only_active_packages_in_active_destinations(self):
        active = make_package()
        make_package(is_active=False)
        make_package(destination=make_destination(is_active=False))
        data = self.client.get(self.url).json()
        self.assertEqual(data["count"], 1)
        self.assertEqual(data["results"][0]["id"], active.pk)

    def test_list_item_has_exactly_the_contract_fields(self):
        package = make_package()
        item = self.client.get(self.url).json()["results"][0]
        self.assertEqual(set(item), LIST_FIELDS)
        self.assertEqual(
            item["destination"],
            {"id": package.destination.pk, "name": package.destination.name},
        )

    def test_price_is_a_string_with_two_decimals(self):
        make_package(price=Decimal("850"))
        item = self.client.get(self.url).json()["results"][0]
        self.assertEqual(item["price"], "850.00")

    def test_list_is_ordered_by_id(self):
        ids = [make_package().pk for _ in range(3)]
        results = [p["id"] for p in self.client.get(self.url).json()["results"]]
        self.assertEqual(results, sorted(ids))

    def test_pagination_page_size_is_12(self):
        destination = make_destination()
        for _ in range(13):
            make_package(destination)
        page1 = self.client.get(self.url).json()
        self.assertEqual(page1["count"], 13)
        self.assertEqual(len(page1["results"]), 12)
        self.assertIsNotNone(page1["next"])
        page2 = self.client.get(self.url, {"page": 2}).json()
        self.assertEqual(len(page2["results"]), 1)
        self.assertIsNone(page2["next"])

    def test_image_is_null_without_upload_and_absolute_with_upload(self):
        make_package()
        self.assertIsNone(self.client.get(self.url).json()["results"][0]["image"])
        TravelPackage.objects.all().delete()
        with temporary_media():
            make_package(image=fake_image("trip.png"))
            image = self.client.get(self.url).json()["results"][0]["image"]
        self.assertTrue(image.startswith("http://testserver/media/packages/trip"))


class PackageFilterTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.dest_a = make_destination(name="Place A")
        cls.dest_b = make_destination(name="Place B")
        cls.cheap = make_package(cls.dest_a, price=Decimal("400.00"), is_featured=False)
        cls.mid = make_package(cls.dest_a, price=Decimal("850.00"), is_featured=True)
        cls.pricey = make_package(cls.dest_b, price=Decimal("1500.00"), is_featured=True)

    def setUp(self):
        self.client = APIClient()
        self.url = reverse("package-list")

    def ids(self, **params):
        return result_ids(self.client.get(self.url, params))

    def test_no_filters_returns_everything(self):
        self.assertEqual(
            self.ids(), {self.cheap.pk, self.mid.pk, self.pricey.pk}
        )

    def test_filter_by_destination(self):
        self.assertEqual(
            self.ids(destination=self.dest_a.pk), {self.cheap.pk, self.mid.pk}
        )
        self.assertEqual(self.ids(destination=self.dest_b.pk), {self.pricey.pk})

    def test_unknown_destination_returns_an_empty_list(self):
        response = self.client.get(self.url, {"destination": 9999})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["count"], 0)

    def test_filter_featured_true_and_false(self):
        self.assertEqual(self.ids(featured="true"), {self.mid.pk, self.pricey.pk})
        self.assertEqual(self.ids(featured="false"), {self.cheap.pk})

    def test_unrecognised_featured_value_is_ignored(self):
        self.assertEqual(
            self.ids(featured="abc"), {self.cheap.pk, self.mid.pk, self.pricey.pk}
        )

    def test_min_price_is_inclusive(self):
        self.assertEqual(self.ids(min_price=850), {self.mid.pk, self.pricey.pk})

    def test_max_price_is_inclusive(self):
        self.assertEqual(self.ids(max_price=850), {self.cheap.pk, self.mid.pk})

    def test_min_and_max_price_combine(self):
        self.assertEqual(self.ids(min_price=500, max_price=1000), {self.mid.pk})

    def test_filters_combine_with_each_other(self):
        self.assertEqual(
            self.ids(destination=self.dest_a.pk, featured="true"), {self.mid.pk}
        )

    def test_invalid_numbers_return_400(self):
        for params in (
            {"min_price": "abc"},
            {"max_price": "abc"},
            {"destination": "abc"},
        ):
            response = self.client.get(self.url, params)
            self.assertEqual(response.status_code, 400, params)
            self.assertIn(next(iter(params)), response.json())


class PackageDetailApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def detail(self, package):
        return self.client.get(reverse("package-detail", args=[package.pk]))

    def test_detail_has_exactly_the_contract_fields(self):
        response = self.detail(make_package())
        self.assertEqual(response.status_code, 200)
        self.assertEqual(set(response.json()), DETAIL_FIELDS)

    def test_includes_and_excludes_are_arrays_of_strings(self):
        package = make_package(includes="Park fees\nMeals", excludes="Flights\nInsurance")
        data = self.detail(package).json()
        self.assertEqual(data["includes"], ["Park fees", "Meals"])
        self.assertEqual(data["excludes"], ["Flights", "Insurance"])

    def test_itinerary_is_ordered_by_day_with_contract_keys(self):
        package = make_package()
        ItineraryDay.objects.create(package=package, day=2, title="Game drives", description="Two.")
        ItineraryDay.objects.create(package=package, day=1, title="Arrival", description="One.")
        itinerary = self.detail(package).json()["itinerary"]
        self.assertEqual([d["day"] for d in itinerary], [1, 2])
        self.assertEqual(set(itinerary[0]), {"day", "title", "description"})

    def test_itinerary_is_empty_list_when_none(self):
        self.assertEqual(self.detail(make_package()).json()["itinerary"], [])

    def test_detail_includes_max_group_size(self):
        data = self.detail(make_package(max_group_size=6)).json()
        self.assertEqual(data["max_group_size"], 6)

    def test_inactive_package_is_404(self):
        self.assertEqual(self.detail(make_package(is_active=False)).status_code, 404)

    def test_package_in_inactive_destination_is_404(self):
        package = make_package(destination=make_destination(is_active=False))
        self.assertEqual(self.detail(package).status_code, 404)

    def test_unknown_id_is_404(self):
        response = self.client.get(reverse("package-detail", args=[9999]))
        self.assertEqual(response.status_code, 404)

    def test_write_methods_are_not_allowed(self):
        package = make_package()
        urls = (
            reverse("package-list"),
            reverse("package-detail", args=[package.pk]),
        )
        for url in urls:
            for method in ("post", "put", "patch", "delete"):
                response = getattr(self.client, method)(url, {}, format="json")
                self.assertEqual(
                    response.status_code, 405, f"{method.upper()} {url}"
                )
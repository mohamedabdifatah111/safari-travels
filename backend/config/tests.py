from django.conf import settings
from django.db import connection
from django.test import TestCase, override_settings

ALLOWED_ORIGIN = "http://localhost:5173"


class DatabaseTests(TestCase):
    def test_postgresql_is_the_only_database(self):
        self.assertEqual(set(settings.DATABASES), {"default"})
        self.assertEqual(
            settings.DATABASES["default"]["ENGINE"], "django.db.backends.postgresql"
        )
        self.assertEqual(connection.vendor, "postgresql")


class ApiErrorTests(TestCase):
    def test_unknown_api_url_returns_json_404(self):
        response = self.client.get("/api/nothing-here/")
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response["Content-Type"], "application/json")
        self.assertEqual(response.json(), {"detail": "Not found."})

    def test_non_api_404_is_not_json(self):
        response = self.client.get("/nothing-here/")
        self.assertEqual(response.status_code, 404)
        self.assertIn("text/html", response["Content-Type"])

    def test_api_responses_are_json(self):
        response = self.client.get("/api/destinations/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/json")

    def test_nosniff_header_is_sent(self):
        response = self.client.get("/api/destinations/")
        self.assertEqual(response["X-Content-Type-Options"], "nosniff")


@override_settings(CORS_ALLOWED_ORIGINS=[ALLOWED_ORIGIN])
class CorsTests(TestCase):
    def preflight(self, origin):
        return self.client.options(
            "/api/bookings/",
            HTTP_ORIGIN=origin,
            HTTP_ACCESS_CONTROL_REQUEST_METHOD="POST",
            HTTP_ACCESS_CONTROL_REQUEST_HEADERS="content-type",
        )

    def test_frontend_origin_is_allowed(self):
        response = self.preflight(ALLOWED_ORIGIN)
        self.assertEqual(response["Access-Control-Allow-Origin"], ALLOWED_ORIGIN)

    def test_other_origins_are_not_allowed(self):
        response = self.preflight("http://evil.example")
        self.assertNotIn("Access-Control-Allow-Origin", response)

    def test_normal_api_responses_include_the_cors_header(self):
        response = self.client.get("/api/destinations/", HTTP_ORIGIN=ALLOWED_ORIGIN)
        self.assertEqual(response["Access-Control-Allow-Origin"], ALLOWED_ORIGIN)
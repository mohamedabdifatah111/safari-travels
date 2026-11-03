"""
JSON error responses for the API.

Django's default 404 and 500 pages are HTML. For URLs under /api/ we return
JSON instead (same shape as DRF's own errors). Other URLs, such as the admin,
keep Django's normal pages. These handlers only run when DEBUG is False.
"""
from django.http import JsonResponse
from django.views import defaults


def _is_api_request(request):
    return request.path.startswith("/api/")


def not_found(request, exception, template_name="404.html"):
    if _is_api_request(request):
        return JsonResponse({"detail": "Not found."}, status=404)
    return defaults.page_not_found(request, exception, template_name=template_name)


def server_error(request, template_name="500.html"):
    if _is_api_request(request):
        return JsonResponse({"detail": "A server error occurred."}, status=500)
    return defaults.server_error(request, template_name=template_name)
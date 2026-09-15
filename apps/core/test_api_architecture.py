from django.test import SimpleTestCase
from django.urls import URLPattern, URLResolver, get_resolver
from rest_framework.views import APIView


class APIViewArchitectureTests(SimpleTestCase):
    def iter_routes(self, patterns, prefix=""):
        for pattern in patterns:
            route = f"{prefix}{pattern.pattern}"
            if isinstance(pattern, URLResolver):
                yield from self.iter_routes(pattern.url_patterns, route)
            elif isinstance(pattern, URLPattern):
                yield route, pattern.callback

    def test_all_application_api_routes_use_apiview(self):
        api_routes = [
            (route, callback)
            for route, callback in self.iter_routes(
                get_resolver().url_patterns
            )
            if route.startswith("api/v1/")
        ]
        self.assertTrue(api_routes)

        for route, callback in api_routes:
            view_class = getattr(callback, "view_class", None) or getattr(
                callback,
                "cls",
                None,
            )
            self.assertIsNotNone(
                view_class,
                msg=f"{route} is not implemented as a class-based APIView.",
            )
            self.assertTrue(
                issubclass(view_class, APIView),
                msg=f"{route} does not inherit from APIView.",
            )
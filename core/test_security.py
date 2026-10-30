"""Cookie regression checks; no real accounts, database writes, or integrations."""

import os
from pathlib import Path
import runpy
from unittest.mock import patch

from django.http import HttpResponse
from django.middleware.csrf import get_token
from django.test import Client, SimpleTestCase, override_settings
from django.urls import path


def cookie_probe(request):
    get_token(request)
    request.session["security_probe"] = True
    return HttpResponse("ok")


urlpatterns = [path("security-probe/", cookie_probe)]


def load_cookie_settings(environment):
    settings_path = Path(__file__).resolve().parents[1] / "site_config" / "settings.py"
    with patch.dict(os.environ, environment, clear=True), patch("dotenv.load_dotenv"):
        values = runpy.run_path(str(settings_path))
    return {name: values[name] for name in ("CSRF_COOKIE_SECURE", "SESSION_COOKIE_SECURE")}


class CookieDefaultsTests(SimpleTestCase):
    def test_production_defaults_protect_both_cookies(self):
        self.assertEqual(load_cookie_settings({}), {
            "CSRF_COOKIE_SECURE": True, "SESSION_COOKIE_SECURE": True,
        })

    def test_local_debug_supports_http(self):
        self.assertEqual(load_cookie_settings({"DEBUG": "true"}), {
            "CSRF_COOKIE_SECURE": False, "SESSION_COOKIE_SECURE": False,
        })

    def test_explicit_https_settings_work_in_debug(self):
        self.assertEqual(load_cookie_settings({
            "DEBUG": "true", "CSRF_COOKIE_SECURE": "True", "SESSION_COOKIE_SECURE": "1",
        }), {"CSRF_COOKIE_SECURE": True, "SESSION_COOKIE_SECURE": True})


@override_settings(
    ROOT_URLCONF=__name__,
    ALLOWED_HOSTS=["testserver"],
    SESSION_ENGINE="django.contrib.sessions.backends.signed_cookies",
    MIDDLEWARE=[
        "django.contrib.sessions.middleware.SessionMiddleware",
        "django.middleware.csrf.CsrfViewMiddleware",
    ],
)
class HttpsCookieFlowTests(SimpleTestCase):
    def setUp(self):
        self.cookie_settings = override_settings(**load_cookie_settings({"DEBUG": "False"}))
        self.cookie_settings.enable()
        self.addCleanup(self.cookie_settings.disable)
        self.client = Client(enforce_csrf_checks=True)

    def test_https_sets_secure_csrf_and_session_cookies(self):
        response = self.client.get("/security-probe/", secure=True)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.cookies["csrftoken"]["secure"])
        self.assertTrue(response.cookies["sessionid"]["secure"])
        self.assertTrue(response.cookies["sessionid"]["httponly"])

    def test_same_origin_https_post_still_works(self):
        self.client.get("/security-probe/", secure=True)
        response = self.client.post(
            "/security-probe/", secure=True,
            HTTP_ORIGIN="https://testserver",
            HTTP_X_CSRFTOKEN=self.client.cookies["csrftoken"].value,
        )
        self.assertEqual(response.status_code, 200)

    def test_missing_csrf_token_is_rejected(self):
        self.client.get("/security-probe/", secure=True)
        response = self.client.post("/security-probe/", secure=True, HTTP_ORIGIN="https://testserver")
        self.assertEqual(response.status_code, 403)

    def test_untrusted_origin_is_rejected(self):
        self.client.get("/security-probe/", secure=True)
        response = self.client.post(
            "/security-probe/", secure=True,
            HTTP_ORIGIN="https://untrusted.example",
            HTTP_X_CSRFTOKEN=self.client.cookies["csrftoken"].value,
        )
        self.assertEqual(response.status_code, 403)

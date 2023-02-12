from __future__ import annotations

from django_upgrade.data import Settings
from tests.fixers.tools import check_noop
from tests.fixers.tools import check_transformed

settings = Settings(target_version=(4, 2))


def test_transform_constructor_call():
    check_transformed(
        """\
        from django.test import RequestFactory
        RequestFactory(HTTP_HOST="test.com")
        """,
        """\
        from django.test import RequestFactory
        RequestFactory(headers={"host": "test.com"})
        """,
        settings,
    )


def test_transform_constructor_call_multiple():
    check_transformed(
        """\
        from django.test import Client
        c = Client(HTTP_HOST="test.com", headers={"user-agent": "example"}, HTTP_ACCEPT_LANGUAGE="fr-fr")
        """,  # noqa: E501
        """\
        from django.test import Client
        c = Client(headers={"user-agent": "example", "host": "test.com", "accept-language": "fr-fr"}, )
        """,  # noqa: E501
        settings,
    )


def test_transform():
    check_transformed(
        """\
        from django.test import Client
        self.client = Client()
        self.client.get("/", HTTP_HOST="test.com", SCRIPT_NAME="/app/")
        """,
        """\
        from django.test import Client
        self.client = Client()
        self.client.get("/", headers={"host": "test.com"}, SCRIPT_NAME="/app/")
        """,
        settings,
    )


def test_transform_only():
    check_transformed(
        """\
        from django.test import Client
        self.client = Client()
        self.client.get("/", HTTP_HOST="test.com")
        """,
        """\
        from django.test import Client
        self.client = Client()
        self.client.get("/", headers={"host": "test.com"})
        """,
        settings,
    )


def test_transform_multiple():
    check_transformed(
        """\
        from django.test import Client
        self.client = Client()
        self.client.get("/", HTTP_HOST="test.com", HTTP_ACCEPT="application/json")
        """,
        """\
        from django.test import Client
        self.client = Client()
        self.client.get("/", headers={"host": "test.com", "accept": "application/json"})
        """,
        settings,
    )


def test_unchanged_parameter():
    check_noop(
        """
        self.client.get("/", SCRIPT_NAME="/app/"),
        """,
        settings,
    )


def test_unchanged_other_call():
    check_noop(
        """
        request.META.get("/", HTTP_HOST="host.com"),
        """,
        settings,
    )


def test_transform_multiline():
    check_transformed(
        """
        response = self.client.post(
            "/password_reset/",
            {"email": "staffmember@example.com"},
            HTTP_HOST="www.example:dr.frankenstein@evil.tld",
        )
        """,
        """
        response = self.client.post(
            "/password_reset/",
            {"email": "staffmember@example.com"},
            headers={"host": "www.example:dr.frankenstein@evil.tld"}
        )
        """,
        settings,
    )

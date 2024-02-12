from __future__ import annotations

import sys
from functools import partial

import pytest

from django_upgrade.data import Settings
from tests.fixers import tools

if sys.version_info < (3, 9):
    pytest.skip("Python 3.9+", allow_module_level=True)

settings = Settings(target_version=(4, 2))
check_noop = partial(tools.check_noop, settings=settings)
check_transformed = partial(tools.check_transformed, settings=settings)


def test_non_test_file():
    check_noop(
        """\
        self.client.get("/", HTTP_HOST="example.com")
        """,
    )


def test_instantiation_custom_client_class():
    check_noop(
        """
        from example.test import Client
        Client(HTTP_HOST="example.com")
        """,
        filename="tests.py",
    )


def test_instantiation_unpacked_kwargs():
    check_noop(
        """
        from example.test import Client
        Client(**maybe_has_headers, HTTP_HOST="example.com")
        """,
        filename="tests.py",
    )


def test_custom_client_call():
    check_noop(
        """
        self.custom_client.get("/", HTTP_HOST="example.com"),
        """,
        filename="tests.py",
    )


def test_client_call_non_http_kwarg():
    check_noop(
        """
        self.client.get("/", SCRIPT_NAME="/app/"),
        """,
        filename="tests.py",
    )


def test_client_call_unpacked_kwargs():
    check_noop(
        """
        self.client.get("/", HTTP_ACCEPT="text/plain", **maybe_has_headers)
        """,
        filename="tests.py",
    )


def test_instantiation_request_factory():
    check_transformed(
        """\
        from django.test import RequestFactory
        RequestFactory(HTTP_HOST="example.com")
        """,
        """\
        from django.test import RequestFactory
        RequestFactory(headers={"host": "example.com"})
        """,
        filename="tests.py",
    )


def test_instantiation():
    check_transformed(
        """\
        from django.test import Client
        Client(HTTP_HOST="example.com")
        """,
        """\
        from django.test import Client
        Client(headers={"host": "example.com"})
        """,
        filename="tests.py",
    )


def test_instantiation_other_arg():
    check_transformed(
        """\
        from django.test import Client
        Client(enforce_csrf_checks=False, HTTP_HOST="example.com")
        """,
        """\
        from django.test import Client
        Client(enforce_csrf_checks=False, headers={"host": "example.com"})
        """,
        filename="tests.py",
    )


def test_instantiation_multiline():
    check_transformed(
        """\
        from django.test import Client
        Client(
            HTTP_HOST="example.com"
        )
        """,
        """\
        from django.test import Client
        Client(
            headers={"host": "example.com"}
        )
        """,
        filename="tests.py",
    )


def test_instantiation_multiple():
    check_transformed(
        """\
        from django.test import Client
        Client(HTTP_A="1", HTTP_B="2")
        """,
        """\
        from django.test import Client
        Client(headers={"a": "1", "b": "2"})
        """,
        filename="tests.py",
    )


def test_instantiation_multiple_surrounding_existing():
    check_transformed(
        """\
        from django.test import Client
        Client(HTTP_A="1", headers={"b": "2"}, HTTP_C="3")
        """,
        """\
        from django.test import Client
        Client(headers={"b": "2", "a": "1", "c": "3"}, )
        """,
        filename="tests.py",
    )


def test_instantiation_multiple_before_existing():
    check_transformed(
        """\
        from django.test import Client
        Client(HTTP_A="1", HTTP_B="2", headers={"c": "3"})
        """,
        """\
        from django.test import Client
        Client(headers={"c": "3", "a": "1", "b": "2"})
        """,
        filename="tests.py",
    )


def test_instantiation_multiple_after_existing():
    check_transformed(
        """\
        from django.test import Client
        Client(headers={"c": "3"}, HTTP_A="1", HTTP_B="2")
        """,
        """\
        from django.test import Client
        Client(headers={"c": "3", "a": "1", "b": "2"}, )
        """,
        filename="tests.py",
    )


def test_instantiation_unpacked_args():
    check_transformed(
        """\
        from django.test import Client
        Client(*args, HTTP_HOST="example.com")
        """,
        """\
        from django.test import Client
        Client(*args, headers={"host": "example.com"})
        """,
        filename="tests.py",
    )


def test_instantiation_existing_empty():
    check_transformed(
        """\
        from django.test import Client
        Client(HTTP_A="1", headers={})
        """,
        """\
        from django.test import Client
        Client(headers={"a": "1"})
        """,
        filename="tests.py",
    )


def test_instantiation_existing_comment():
    check_transformed(
        """\
        from django.test import Client
        Client(
            HTTP_A="1",
            headers={
                # todo: add headers
            }
        )
        """,
        """\
        from django.test import Client
        Client(
            headers={
                # todo: add headers
            "a": "1"}
        )
        """,
        filename="tests.py",
    )


def test_instantiation_existing_variable():
    check_noop(
        """\
        from django.test import Client
        headers = {}
        Client(HTTP_A="1", headers=headers)
        """,
        filename="tests.py",
    )


def test_instantiation_existing_dict_comp():
    check_noop(
        """\
        from django.test import Client
        names = ["header1"]
        Client(HTTP_A="1", headers={h: "yes" for h in names})
        """,
        filename="tests.py",
    )


def test_client_call():
    check_transformed(
        """\
        self.client.get("/", HTTP_HOST="example.com")
        """,
        """\
        self.client.get("/", headers={"host": "example.com"})
        """,
        filename="tests.py",
    )


def test_client_call_multiple():
    check_transformed(
        """\
        self.client.get("/", HTTP_HOST="example.com", HTTP_ACCEPT="text/plain")
        """,
        """\
        self.client.get("/", headers={"host": "example.com", "accept": "text/plain"})
        """,
        filename="tests.py",
    )


def test_client_call_extra_arg():
    check_transformed(
        """\
        self.client.get("/", HTTP_HOST="example.com", SCRIPT_NAME="/app/")
        """,
        """\
        self.client.get("/", headers={"host": "example.com"}, SCRIPT_NAME="/app/")
        """,
        filename="tests.py",
    )


def test_client_call_unpacked_args():
    check_transformed(
        """\
        self.client.get(*args, HTTP_HOST="example.com")
        """,
        """\
        self.client.get(*args, headers={"host": "example.com"})
        """,
        filename="tests.py",
    )


def test_client_call_extra_arg_in_between():
    check_transformed(
        """\
        self.client.get("/", HTTP_A="1", SCRIPT_NAME="/app/", HTTP_B="2")
        """,
        """\
        self.client.get("/", headers={"a": "1", "b": "2"}, SCRIPT_NAME="/app/", )
        """,
        filename="tests.py",
    )


def test_client_call_multiline():
    check_transformed(
        """
        response = self.client.get(
            "/",
            {"q": "abc"},
            HTTP_HOST="example.com",
        )
        """,
        """
        response = self.client.get(
            "/",
            {"q": "abc"},
            headers={"host": "example.com"}
        )
        """,
        filename="tests.py",
    )


def test_client_call_multiline_comment():
    check_transformed(
        """
        response = self.client.get(
            "/",
            {"q": "abc"},
            HTTP_HOST="example.com",  # set host
        )
        """,
        """
        response = self.client.get(
            "/",
            {"q": "abc"},
            headers={"host": "example.com"}  # set host
        )
        """,
        filename="tests.py",
    )


def test_client_call_multiline_multiple():
    check_transformed(
        """
        response = self.client.get(
            "/",
            {"q": "abc"},
            HTTP_HOST="example.com",
            HTTP_ACCEPT="text/plain",
        )
        """,
        """
        response = self.client.get(
            "/",
            {"q": "abc"},
            headers={"host": "example.com", "accept": "text/plain"}
        )
        """,
        filename="tests.py",
    )


def test_client_variable():
    check_transformed(
        """\
        self.client.get("/", HTTP_HOST=host)
        """,
        """\
        self.client.get("/", headers={"host": host})
        """,
        filename="tests.py",
    )


def test_client_expression():
    check_transformed(
        """\
        self.client.get("/", HTTP_HOST=(name + tld))
        """,
        """\
        self.client.get("/", headers={"host": (name + tld)})
        """,
        filename="tests.py",
    )


def test_client_expression_multiline():
    check_transformed(
        """\
        self.client.get("/", HTTP_HOST=(
            name + tld
        ))
        """,
        """\
        self.client.get("/", headers={"host": (
            name + tld
        )})
        """,
        filename="tests.py",
    )

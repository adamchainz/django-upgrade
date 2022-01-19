from __future__ import annotations

import pytest

from django_upgrade.data import Settings
from django_upgrade.fixers.testcase_databases import looks_like_test_file
from tests.fixers.tools import check_noop, check_transformed

settings = Settings(target_version=(2, 2))


@pytest.mark.parametrize(
    ("filename"),
    (
        "test_example.py",
        "example_test.py",
        "test.py",
        "tests.py",
        "myapp/test.py",
        "myapp/tests.py",
        "myapp/tests/base.py",
        "myapp/tests/__init__.py",
        "myapp/test_example.py",
        "myapp/tests_example.py",
        "myapp/example_test.py",
        "myapp/example_tests.py",
    ),
)
def test_looks_like_test_file_true(filename):
    assert looks_like_test_file(filename)


@pytest.mark.parametrize(
    ("filename"),
    (
        "conftest.py",
        "protester.py",
        "myapp/protests/models.py",
    ),
)
def test_looks_like_test_file_false(filename):
    assert not looks_like_test_file(filename)


def test_not_test_file():
    check_noop(
        """\
        class MyTests:
            allow_database_queries = True
        """,
        settings,
    )


def test_not_in_class_def():
    check_noop(
        """\
        class MyTests:
            pass
        allow_database_queries = True
        """,
        settings,
        filename="tests.py",
    )


def test_simple_test_case_conditional():
    check_noop(
        """\
        from django.test import SimpleTestCase

        class MyTests(SimpleTestCase):
            if django.VERSION >= (2, 2):
                databases = "__all__"
            else:
                allow_database_queries = True

            def test_something(self):
                self.assertEqual(2 * 2, 4)
        """,
        settings,
        filename="tests.py",
    )


def test_simple_test_case_true():
    check_transformed(
        """\
        from django.test import SimpleTestCase

        class MyTests(SimpleTestCase):
            allow_database_queries = True

            def test_something(self):
                self.assertEqual(2 * 2, 4)
        """,
        """\
        from django.test import SimpleTestCase

        class MyTests(SimpleTestCase):
            databases = "__all__"

            def test_something(self):
                self.assertEqual(2 * 2, 4)
        """,
        settings,
        filename="tests.py",
    )


def test_simple_test_case_false():
    check_transformed(
        """\
        from django.test import SimpleTestCase

        class MyTests(SimpleTestCase):
            allow_database_queries = False

            def test_something(self):
                self.assertEqual(2 * 2, 4)
        """,
        """\
        from django.test import SimpleTestCase

        class MyTests(SimpleTestCase):
            databases = []

            def test_something(self):
                self.assertEqual(2 * 2, 4)
        """,
        settings,
        filename="tests.py",
    )


def test_test_case_true():
    check_transformed(
        """\
        from django.test import TestCase

        class MyTests(TestCase):
            multi_db = True

            def test_something(self):
                self.assertEqual(2 * 2, 4)
        """,
        """\
        from django.test import TestCase

        class MyTests(TestCase):
            databases = "__all__"

            def test_something(self):
                self.assertEqual(2 * 2, 4)
        """,
        settings,
        filename="tests.py",
    )


def test_test_case_false():
    check_transformed(
        """\
        from django.test import TestCase

        class MyTests(TestCase):
            multi_db = False

            def test_something(self):
                self.assertEqual(2 * 2, 4)
        """,
        """\
        from django.test import TestCase

        class MyTests(TestCase):
            databases = []

            def test_something(self):
                self.assertEqual(2 * 2, 4)
        """,
        settings,
        filename="tests.py",
    )


def test_mixin():
    check_transformed(
        """\
        class MyTestMixin:
            multi_db = True

            my_custom_property = [True]
        """,
        """\
        class MyTestMixin:
            databases = "__all__"

            my_custom_property = [True]
        """,
        settings,
        filename="tests.py",
    )

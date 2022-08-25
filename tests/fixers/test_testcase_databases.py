from __future__ import annotations

from django_upgrade.data import Settings
from tests.fixers.tools import check_noop, check_transformed

settings = Settings(target_version=(2, 2))


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
            if something:
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

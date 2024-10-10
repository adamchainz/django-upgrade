from __future__ import annotations

from functools import partial

from django_upgrade.data import Settings
from tests.fixers import tools

settings = Settings(target_version=(4, 1))
check_noop = partial(tools.check_noop, settings=settings)
check_transformed = partial(tools.check_transformed, settings=settings)


def test_unittest_skipIf_kept():
    check_noop(
        """\
        import unittest
        import django

        @unittest.skipIf(django.VERSION < (4, 2), "Django 4.2+")
        def test_thing(self):
            pass
        """,
    )


def test_unittest_skip_left():
    check_noop(
        """\
        import unittest

        @unittest.skip("Always skipped")
        def test_thing(self):
            pass
        """,
    )


def test_unittest_skipIf_removed():
    check_transformed(
        """\
        import unittest
        import django

        @unittest.skipIf(django.VERSION < (4, 1), "Django 4.1+")
        def test_thing(self):
            pass
        """,
        """\
        import unittest
        import django

        def test_thing(self):
            pass
        """,
    )


def test_skipUnless_removed():
    check_transformed(
        """\
        import unittest
        import django

        @unittest.skipUnless(django.VERSION >= (4, 1), "Django 4.1+")
        def test_thing(self):
            pass
        """,
        """\
        import unittest
        import django

        def test_thing(self):
            pass
        """,
    )

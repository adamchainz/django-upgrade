from __future__ import annotations

from functools import partial

from django_upgrade.data import Settings
from tests.fixers import tools

settings = Settings(target_version=(4, 1))
check_noop = partial(tools.check_noop, settings=settings)
check_transformed = partial(tools.check_transformed, settings=settings)


def test_unittest_attr_skip_left():
    check_noop(
        """\
        import unittest

        @unittest.skip("Always skipped")
        def test_thing(self):
            pass
        """,
    )


def test_unittest_attr_skipIf_too_few_args():
    check_noop(
        """\
        import unittest
        import django

        @unittest.skipIf(django.VERSION < (4, 1))
        def test_thing(self):
            pass
        """,
    )


def test_unittest_attr_skipIf_too_many_args():
    check_noop(
        """\
        import unittest
        import django

        @unittest.skipIf(django.VERSION < (4, 1), "Django 4.1+", "what is this arg?")
        def test_thing(self):
            pass
        """,
    )


def test_unittest_attr_skipIf_passing_comparison():
    check_noop(
        """\
        import unittest
        import django

        @unittest.skipIf(django.VERSION < (4, 2), "Django 4.2+")
        def test_thing(self):
            pass
        """,
    )


def test_unittest_attr_skipIf_unknown_comparison():
    check_noop(
        """\
        import unittest
        import django

        @unittest.skipIf(django.VERSION < (4, 1, 1), "Django 4.1.1+")
        def test_thing(self):
            pass
        """,
    )


def test_unittest_bare_skipIf_passing_comparison():
    check_noop(
        """\
        from unittest import skipIf
        import django

        @skipIf(django.VERSION < (4, 2), "Django 4.2+")
        def test_thing(self):
            pass
        """,
    )


def test_unittest_attr_skipUnless_failing_comparison():
    check_noop(
        """\
        import unittest
        import django

        @unittest.skipUnless(django.VERSION >= (4, 2), "Django 4.2+")
        def test_thing(self):
            pass
        """,
    )


def test_unittest_bare_skipUnless_failing_comparison():
    check_noop(
        """\
        from unittest import skipUnless
        import django

        @skipUnless(django.VERSION >= (4, 2), "Django 4.2+")
        def test_thing(self):
            pass
        """,
    )


def test_unittest_attr_skipIf_removed():
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


def test_unittest_bare_skipIf_removed():
    check_transformed(
        """\
        from unittest import skipIf
        import django

        @skipIf(django.VERSION < (4, 1), "Django 4.1+")
        def test_thing(self):
            pass
        """,
        """\
        from unittest import skipIf
        import django

        def test_thing(self):
            pass
        """,
    )


def test_unittest_skipIf_mixed():
    check_transformed(
        """\
        import unittest
        from unittest import skipIf
        import django

        @unittest.skipUnless(django.VERSION >= (4, 1), "Django 4.1+")
        @skipIf(django.VERSION < (4, 1), "Django 4.1+")
        def test_thing(self):
            pass
        """,
        """\
        import unittest
        from unittest import skipIf
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


def test_unittest_bare_skipUnless_removed():
    check_transformed(
        """\
        from unittest import skipUnless
        import django

        @skipUnless(django.VERSION >= (4, 1), "Django 4.1+")
        def test_thing(self):
            pass
        """,
        """\
        from unittest import skipUnless
        import django

        def test_thing(self):
            pass
        """,
    )


def test_unittest_bare_skipIf_skipUnless_mixed():
    check_transformed(
        """\
        from unittest import skipIf, skipUnless
        import django

        @skipUnless(django.VERSION >= (4, 1), "Django 4.1+")
        @skipIf(django.VERSION < (4, 1), "Django 4.1+")
        def test_thing(self):
            pass
        """,
        """\
        from unittest import skipIf, skipUnless
        import django

        def test_thing(self):
            pass
        """,
    )

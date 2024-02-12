from __future__ import annotations

from functools import partial

from django_upgrade.data import Settings
from tests.fixers import tools

settings = Settings(target_version=(4, 2))
check_noop = partial(tools.check_noop, settings=settings)
check_transformed = partial(tools.check_transformed, settings=settings)


def test_assertFormsetError_non_test_file():
    check_noop(
        """\
        from django.test import SimpleTestCase

        class MyTest(SimpleTestCase):

            def test_formset_error(self):
                self.assertFormsetError('foo', 'bar')
        """,
    )


def test_assertFormsetError_custom_method():
    check_noop(
        """\
        from django.test import SimpleTestCase

        class MyTest(SimpleTestCase):

            def assertFormsetError(self, foo, bar):
                pass
        """,
        filename="tests.py",
    )


def test_assertFormsetError_transformed():
    check_transformed(
        """\
        from django.test import SimpleTestCase

        class MyTest(SimpleTestCase):

            def test_formset_error(self):
                self.assertFormsetError('foo', 'bar')
        """,
        """\
        from django.test import SimpleTestCase

        class MyTest(SimpleTestCase):

            def test_formset_error(self):
                self.assertFormSetError('foo', 'bar')
        """,
        filename="tests.py",
    )


def test_assertQuerysetEqual_non_test_file():
    check_noop(
        """\
        from django.test import SimpleTestCase

        class MyTest(SimpleTestCase):

            def test_formset_error(self):
                self.assertQuerysetEqual('foo', 'bar')
        """,
    )


def test_assertQuerysetEqual_custom_method():
    check_noop(
        """\
        from django.test import SimpleTestCase

        class MyTest(SimpleTestCase):

            def assertQuerysetEqual(self, foo, bar):
                pass
        """,
    )


def test_assertQuerysetEqual_transformed():
    check_transformed(
        """\
        from django.test import SimpleTestCase

        class MyTest(SimpleTestCase):

            def test_formset_error(self):
                self.assertQuerysetEqual('foo', 'bar')
        """,
        """\
        from django.test import SimpleTestCase

        class MyTest(SimpleTestCase):

            def test_formset_error(self):
                self.assertQuerySetEqual('foo', 'bar')
        """,
        filename="tests.py",
    )

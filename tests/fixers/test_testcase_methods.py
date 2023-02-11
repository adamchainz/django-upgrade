from __future__ import annotations

from django_upgrade.data import Settings
from tests.fixers.tools import check_noop
from tests.fixers.tools import check_transformed

settings = Settings(target_version=(4, 2))


def test_assertFormsetError_not_transformed():
    check_noop(
        """\
        class A:
            def assertFormsetError(foo, bar):
                pass

        a = A()
        a.assertFormsetError('foo', 'bar')
        """,
        settings,
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
        settings,
    )


def test_assertQuerysetEqual_not_transformed():
    check_noop(
        """\
        class A:
            def assertQuerysetEqual(foo, bar):
                pass

        a = A()
        a.assertQuerysetEqual('foo', 'bar')
        """,
        settings,
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
        settings,
    )

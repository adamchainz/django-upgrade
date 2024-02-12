from __future__ import annotations

from functools import partial

from django_upgrade.data import Settings
from tests.fixers import tools

settings = Settings(target_version=(3, 0))
check_noop = partial(tools.check_noop, settings=settings)
check_transformed = partial(tools.check_transformed, settings=settings)


def test_no_deprecated_alias():
    check_noop(
        """\
        from django.utils.translation import something

        something("yada")
        """,
    )


def test_module_imported():
    check_transformed(
        """\
        from django.utils import translation

        translation.ugettext("lala")
        """,
        """\
        from django.utils import translation

        translation.gettext("lala")
        """,
    )


def test_direct_import():
    check_transformed(
        """\
        from django.utils.translation import ugettext_lazy, ugettext_noop

        def main(*, argv):
            print(
                ugettext_lazy("yada"),
                ugettext_noop("yada"),
            )
        """,
        """\
        from django.utils.translation import gettext_lazy, gettext_noop

        def main(*, argv):
            print(
                gettext_lazy("yada"),
                gettext_noop("yada"),
            )
        """,
    )


def test_success_alias():
    check_transformed(
        """\
        from django.utils.translation import ungettext as ng

        ng.__name__
        """,
        """\
        from django.utils.translation import ngettext as ng

        ng.__name__
        """,
    )

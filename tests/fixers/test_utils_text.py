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
        from django.utils.text import something

        something("yada")
        """,
    )


def test_simple():
    check_transformed(
        """\
        from django.utils.text import unescape_entities

        unescape_entities("input string")
        """,
        """\
        import html

        html.escape("input string")
        """,
    )


def test_with_other_import():
    check_transformed(
        """\
        from django.utils.text import unescape_entities, slugify

        unescape_entities("input string")
        """,
        """\
        import html
        from django.utils.text import slugify

        html.escape("input string")
        """,
    )


def test_indented():
    check_transformed(
        """\
        if True:
            from django.utils.text import unescape_entities, slugify

            unescape_entities("input string")
        """,
        """\
        if True:
            import html
            from django.utils.text import slugify

            html.escape("input string")
        """,
    )

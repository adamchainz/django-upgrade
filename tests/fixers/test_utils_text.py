from django_upgrade.data import Settings
from tests.fixers.tools import check_noop, check_transformed

settings = Settings(target_version=(3, 0))


def test_no_deprecated_alias():
    check_noop(
        """\
        from django.utils.text import something

        something("yada")
        """,
        settings,
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
        settings,
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
        settings,
    )

from django_upgrade.data import Settings
from tests.fixers.tools import check_noop, check_transformed

settings = Settings(target_version=(3, 0))


def test_no_deprecated_alias():
    check_noop(
        """\
        from django.utils.encoding import something

        something("yada")
        """,
        settings,
    )


def test_encoding_module_imported():
    check_transformed(
        """\
        from django.utils import encoding

        encoding.force_text("yada")
        encoding.smart_text("yada")
        """,
        """\
        from django.utils import encoding

        encoding.force_str("yada")
        encoding.smart_str("yada")
        """,
        settings,
    )


def test_direct_import():
    check_transformed(
        """\
        from django.utils.encoding import force_text, smart_text

        def main(*, argv):
            print(
                force_text("yada"),
                smart_text("yada"),
            )
        """,
        """\
        from django.utils.encoding import force_str, smart_str

        def main(*, argv):
            print(
                force_str("yada"),
                smart_str("yada"),
            )
        """,
        settings,
    )


def test_success_alias():
    check_transformed(
        """\
        from django.utils.encoding import force_text as ft

        ft("yada")
        """,
        """\
        from django.utils.encoding import force_str as ft

        ft("yada")
        """,
        settings,
    )

from django_upgrade.data import Settings
from tests.fixers.tools import check_transformed

settings = Settings(target_version=(2, 2))


def test_include_import():
    check_transformed(
        """\
        from django.conf.urls import include
        """,
        """\
        from django.urls import include
        """,
        settings,
    )


def test_url_import():
    check_transformed(
        """\
        from django.conf.urls import url
        """,
        """\
        from django.urls import re_path
        """,
        settings,
    )


def test_additional_i18n_patterns_import():
    check_transformed(
        """\
        from django.conf.urls import include, i18n_patterns
        """,
        """\
        from django.urls import include
        from django.conf.urls import i18n_patterns
        """,
        settings,
    )

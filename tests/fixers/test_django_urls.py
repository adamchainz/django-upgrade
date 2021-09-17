from django_upgrade.data import Settings
from tests.fixers.tools import check_noop, check_transformed

settings = Settings(target_version=(2, 2))


def test_unrecognized_import_format():
    check_noop(
        """\
        from django.conf import urls

        urls.url("hahaha")
        """,
        settings,
    )


def test_re_path():
    check_transformed(
        """\
        from django.conf.urls import url

        url(r'^[abc]{123}$', views.example)
        """,
        """\
        from django.urls import re_path

        re_path(r'^[abc]{123}$', views.example)
        """,
        settings,
    )


def test_path_simple():
    check_transformed(
        """\
        from django.conf.urls import url

        url(r"^$", views.index)
        """,
        """\
        from django.urls import path

        path('', views.index)
        """,
        settings,
    )

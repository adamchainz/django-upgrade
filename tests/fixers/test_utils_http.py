from django_upgrade.data import Settings
from tests.fixers.tools import check_noop, check_transformed

settings = Settings(target_version=(3, 0))


def test_no_deprecated_alias():
    check_noop(
        """\
        from django.utils.http import something

        something
        """,
        settings,
    )


def test_one_local_name():
    check_transformed(
        """\
        from django.utils.http import is_safe_url

        x = is_safe_url(y)
        """,
        """\
        from django.utils.http import url_has_allowed_host_and_scheme

        x = url_has_allowed_host_and_scheme(y)
        """,
        settings,
    )


def test_one_urllib_name():
    check_transformed(
        """\
        from django.utils.http import urlquote

        x = urlquote(y)
        """,
        """\
        from urllib.parse import quote

        x = quote(y)
        """,
        settings,
    )


def test_one_urllib_name_indented():
    check_transformed(
        """\
        if True:
            from django.utils.http import urlquote
        """,
        """\
        if True:
            from urllib.parse import quote
        """,
        settings,
    )


def test_all_names():
    check_transformed(
        """\
        from django.utils.http import (
            urlquote, urlquote_plus, urlunquote, urlunquote_plus
        )

        urlquote(urlquote_plus(urlunquote(urlunquote_plus(21))))
        """,
        """\
        from urllib.parse import quote, quote_plus, unquote, unquote_plus

        quote(quote_plus(unquote(unquote_plus(21))))
        """,
        settings,
    )


def test_all_names_different_format():
    check_transformed(
        """\
        from django.utils.http import (
            urlquote, # hi
                urlquote_plus, # yo
                    urlunquote, # huh
                        urlunquote_plus #??
        )

        urlquote(urlquote_plus(urlunquote(urlunquote_plus(21))))
        """,
        """\
        from urllib.parse import quote, quote_plus, unquote, unquote_plus

        quote(quote_plus(unquote(unquote_plus(21))))
        """,
        settings,
    )


def test_single_alias():
    check_transformed(
        """\
        from django.utils.http import urlquote as q

        v = q("x")
        """,
        """\
        from urllib.parse import quote as q

        v = q("x")
        """,
        settings,
    )


def test_mixed_aliases():
    check_transformed(
        """\
        from django.utils.http import (
            urlunquote, urlquote_plus as qp, urlquote as q, urlunquote_plus
        )

        v = q("x")
        """,
        """\
        from urllib.parse import unquote, quote_plus as qp, quote as q, unquote_plus

        v = q("x")
        """,
        settings,
    )

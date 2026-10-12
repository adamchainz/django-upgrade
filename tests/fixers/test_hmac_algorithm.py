from __future__ import annotations

from functools import partial

from django_upgrade.data import Settings
from tests.fixers import tools

settings = Settings(target_version=(6, 1))
check_noop = partial(tools.check_noop, settings=settings)
check_transformed = partial(tools.check_transformed, settings=settings)


def test_old_target_version():
    tools.check_noop(
        """\
        from django.utils.crypto import salted_hmac

        salted_hmac("salt", value)
        """,
        settings=Settings(target_version=(6, 0)),
    )


def test_unrelated_import():
    check_noop(
        """\
        from example import salted_hmac

        salted_hmac("salt", value)
        """,
    )


def test_unimported_name():
    check_noop(
        """\
        salted_hmac("salt", value)
        """,
    )


def test_attribute_access_unrelated_module():
    check_noop(
        """\
        from example import crypto

        crypto.salted_hmac("salt", value)
        """,
    )


def test_salted_hmac_imported():
    check_transformed(
        """\
        from django.utils.crypto import salted_hmac

        salted_hmac("salt", value)
        """,
        """\
        from django.utils.crypto import salted_hmac

        salted_hmac("salt", value, algorithm="sha1")
        """,
    )


def test_salted_hmac_module_imported():
    check_transformed(
        """\
        from django.utils import crypto

        crypto.salted_hmac("salt", value)
        """,
        """\
        from django.utils import crypto

        crypto.salted_hmac("salt", value, algorithm="sha1")
        """,
    )


def test_salted_hmac_with_secret():
    check_transformed(
        """\
        from django.utils.crypto import salted_hmac

        salted_hmac("salt", value, "secret")
        """,
        """\
        from django.utils.crypto import salted_hmac

        salted_hmac("salt", value, "secret", algorithm="sha1")
        """,
    )


def test_salted_hmac_with_keyword_arguments():
    check_transformed(
        """\
        from django.utils.crypto import salted_hmac

        salted_hmac("salt", value, secret="secret")
        """,
        """\
        from django.utils.crypto import salted_hmac

        salted_hmac("salt", value, secret="secret", algorithm="sha1")
        """,
    )


def test_salted_hmac_with_trailing_comma():
    check_transformed(
        """\
        from django.utils.crypto import salted_hmac

        salted_hmac("salt", value,)
        """,
        """\
        from django.utils.crypto import salted_hmac

        salted_hmac("salt", value, algorithm="sha1")
        """,
    )


def test_salted_hmac_no_arguments():
    # A call without arguments still produces valid code.
    check_transformed(
        """\
        from django.utils.crypto import salted_hmac

        salted_hmac()
        """,
        """\
        from django.utils.crypto import salted_hmac

        salted_hmac(algorithm="sha1")
        """,
    )


def test_salted_hmac_multiline():
    check_transformed(
        """\
        from django.utils.crypto import salted_hmac

        salted_hmac(
            "salt",
            value,
        )
        """,
        """\
        from django.utils.crypto import salted_hmac

        salted_hmac(
            "salt",
            value,
         algorithm="sha1")
        """,
    )


def test_salted_hmac_explicit_algorithm():
    check_noop(
        """\
        from django.utils.crypto import salted_hmac

        salted_hmac("salt", value, algorithm="sha256")
        """,
    )


def test_salted_hmac_star_unpacking():
    # algorithm is keyword-only for salted_hmac(), so *args cannot provide it.
    check_transformed(
        """\
        from django.utils.crypto import salted_hmac

        salted_hmac(*args)
        """,
        """\
        from django.utils.crypto import salted_hmac

        salted_hmac(*args, algorithm="sha1")
        """,
    )


def test_salted_hmac_double_star_unpacking():
    check_noop(
        """\
        from django.utils.crypto import salted_hmac

        salted_hmac("salt", value, **kwargs)
        """,
    )


def test_base64_hmac_imported():
    check_transformed(
        """\
        from django.core.signing import base64_hmac

        base64_hmac("salt", value, key)
        """,
        """\
        from django.core.signing import base64_hmac

        base64_hmac("salt", value, key, algorithm="sha1")
        """,
    )


def test_base64_hmac_module_imported():
    check_transformed(
        """\
        from django.core import signing

        signing.base64_hmac("salt", value, key)
        """,
        """\
        from django.core import signing

        signing.base64_hmac("salt", value, key, algorithm="sha1")
        """,
    )


def test_base64_hmac_positional_algorithm():
    check_noop(
        """\
        from django.core.signing import base64_hmac

        base64_hmac("salt", value, key, "sha256")
        """,
    )


def test_base64_hmac_explicit_algorithm():
    check_noop(
        """\
        from django.core.signing import base64_hmac

        base64_hmac("salt", value, key, algorithm="sha256")
        """,
    )


def test_base64_hmac_star_unpacking():
    check_noop(
        """\
        from django.core.signing import base64_hmac

        base64_hmac(*args)
        """,
    )


def test_base64_hmac_double_star_unpacking():
    check_noop(
        """\
        from django.core.signing import base64_hmac

        base64_hmac("salt", value, key, **kwargs)
        """,
    )

from django_upgrade.data import Settings
from tests.fixers.tools import check_noop, check_transformed

settings = Settings(target_version=(3, 1))


def test_providing_length_as_pos_arg():
    check_noop(
        """\
        from django.utils.crypto import get_random_string
        get_random_string(12)
        """,
        settings,
    )


def test_providing_length_as_pos_arg_module():
    check_noop(
        """\
        from django.utils import crypto
        crypto.get_random_string(12)
        """,
        settings,
    )


def test_providing_length_as_kwarg():
    check_noop(
        """\
        from django.utils.crypto import get_random_string
        get_random_string(length=12)
        """,
        settings,
    )


def test_no_pos_arg():
    check_transformed(
        """\
        from django.utils.crypto import get_random_string
        my_password = get_random_string() + "!"
        """,
        """\
        from django.utils.crypto import get_random_string
        my_password = get_random_string(length=12) + "!"
        """,
        settings,
    )


def test_no_pos_arg_module_imported():
    check_transformed(
        """\
        from django.utils import crypto
        my_password = crypto.get_random_string() + "!"
        """,
        """\
        from django.utils import crypto
        my_password = crypto.get_random_string(length=12) + "!"
        """,
        settings,
    )


def test_no_pos_arg_with_allowed_chars():
    check_transformed(
        """\
        from django.utils.crypto import get_random_string
        my_password = get_random_string(allowed_chars="123") + "!"
        """,
        """\
        from django.utils.crypto import get_random_string
        my_password = get_random_string(length=12, allowed_chars="123") + "!"
        """,
        settings,
    )

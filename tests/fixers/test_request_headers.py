from django_upgrade.data import Settings
from tests.fixers.tools import check_noop, check_transformed

settings = Settings(target_version=(2, 2))


def test_not_header_access():
    check_noop(
        """\
        request.META['CONTENT_LENGTH']
        """,
        settings,
    )


def test_subscript_simple():
    check_transformed(
        """\
        request.META['HTTP_SERVER']
        """,
        """\
        request.headers['Server']
        """,
        settings,
    )


def test_subscript_two_words():
    check_transformed(
        """\
        request.META['HTTP_ACCEPT_ENCODING']
        """,
        """\
        request.headers['Accept-Encoding']
        """,
        settings,
    )


def test_subscript_three_words():
    check_transformed(
        """\
        request.META['HTTP_X_POWERED_BY']
        """,
        """\
        request.headers['X-Powered-By']
        """,
        settings,
    )


def test_subscript_self_request():
    check_transformed(
        """\
        self.request.META['HTTP_ACCEPT_ENCODING']
        """,
        """\
        self.request.headers['Accept-Encoding']
        """,
        settings,
    )


def test_get_simple():
    check_transformed(
        """\
        request.META.get('HTTP_SERVER')
        """,
        """\
        request.headers.get('Server')
        """,
        settings,
    )


def test_get_default():
    check_transformed(
        """\
        request.META.get('HTTP_SERVER', '')
        """,
        """\
        request.headers.get('Server', '')
        """,
        settings,
    )


def test_get_self_request():
    check_transformed(
        """\
        request.META.get('HTTP_SERVER')
        """,
        """\
        request.headers.get('Server')
        """,
        settings,
    )

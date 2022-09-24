from __future__ import annotations

from django_upgrade.data import Settings
from tests.fixers.tools import check_noop, check_transformed

settings = Settings(target_version=(2, 2))


def test_not_header_access():
    check_noop(
        """\
        request.META['QUERY_STRING']
        """,
        settings,
    )


def test_not_string():
    check_noop(
        """\
        request.META[123]
        """,
        settings,
    )


def test_assignment():
    check_noop(
        """\
        request.META['HTTP_SERVER'] = 'something'
        """,
        settings,
    )


def test_in_not_header():
    check_noop(
        """\
        'QUERY_STRING' in request.META
        """,
        settings,
    )


def test_not_in_not_header():
    check_noop(
        """\
        'QUERY_STRING' not in request.META
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


def test_get_content_length():
    check_transformed(
        """\
        request.META.get('CONTENT_LENGTH')
        """,
        """\
        request.headers.get('Content-Length')
        """,
        settings,
    )


def test_get_content_type():
    check_transformed(
        """\
        request.META.get('CONTENT_TYPE')
        """,
        """\
        request.headers.get('Content-Type')
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


def test_in():
    check_transformed(
        """\
        'HTTP_AUTHORIZATION' in request.META
        """,
        """\
        'Authorization' in request.headers
        """,
        settings,
    )


def test_in_within_if():
    check_transformed(
        """\
        if 'HTTP_AUTHORIZATION' in request.META:
            print('hi')
        """,
        """\
        if 'Authorization' in request.headers:
            print('hi')
        """,
        settings,
    )


def test_in_get_combined():
    check_transformed(
        """\
        if 'HTTP_AUTHORIZATION' in request.META:
            print(request.META.get('HTTP_AUTHORIZATION'))
        """,
        """\
        if 'Authorization' in request.headers:
            print(request.headers.get('Authorization'))
        """,
        settings,
    )


def test_in_double_statement():
    check_transformed(
        """\
        if 'HTTP_AUTHORIZATION' in request.META and 'HTTP_SERVER' in request.META:
            print('hi')
        """,
        """\
        if 'Authorization' in request.headers and 'Server' in request.headers:
            print('hi')
        """,
        settings,
    )


def test_not_in():
    check_transformed(
        """\
        'HTTP_SERVER' not in request.META
        """,
        """\
        'Server' not in request.headers
        """,
        settings,
    )


def test_not_in_within_if():
    check_transformed(
        """\
        if 'HTTP_AUTHORIZATION' not in request.META:
            print('hi')
        """,
        """\
        if 'Authorization' not in request.headers:
            print('hi')
        """,
        settings,
    )


def test_not_in_get_combined():
    check_transformed(
        """\
        if 'HTTP_AUTHORIZATION' not in request.META:
            print(request.META.get('HTTP_AUTHORIZATION'))
        """,
        """\
        if 'Authorization' not in request.headers:
            print(request.headers.get('Authorization'))
        """,
        settings,
    )


def test_not_in_double_statement():
    check_transformed(
        """\
        if 'HTTP_AUTHORIZATION' not in request.META and \
              'HTTP_SERVER' not in request.META:
            print('hi')
        """,
        """\
        if 'Authorization' not in request.headers and \
              'Server' not in request.headers:
            print('hi')
        """,
        settings,
    )

from __future__ import annotations

from functools import partial

from django_upgrade.data import Settings
from tests.fixers import tools

settings = Settings(target_version=(2, 2))
check_noop = partial(tools.check_noop, settings=settings)
check_transformed = partial(tools.check_transformed, settings=settings)


def test_not_header_access():
    check_noop(
        """\
        request.META['QUERY_STRING']
        """,
    )


def test_not_string():
    check_noop(
        """\
        request.META[123]
        """,
    )


def test_assignment():
    check_noop(
        """\
        request.META['HTTP_SERVER'] = 'something'
        """,
    )


def test_delete():
    check_noop(
        """\
        del request.META['HTTP_SERVER']
        """,
    )


def test_in_not_header():
    check_noop(
        """\
        'QUERY_STRING' in request.META
        """,
    )


def test_not_in_not_header():
    check_noop(
        """\
        'QUERY_STRING' not in request.META
        """,
    )


def test_subscript_simple():
    check_transformed(
        """\
        request.META['HTTP_SERVER']
        """,
        """\
        request.headers['server']
        """,
    )


def test_subscript_assigned():
    check_transformed(
        """\
        server = request.META['HTTP_SERVER']
        """,
        """\
        server = request.headers['server']
        """,
    )


def test_subscript_assigned_multiple():
    check_transformed(
        """\
        server, powered_by = (
            request.META['HTTP_SERVER'],
            request.META['HTTP_X_POWERED_BY'],
        )
        """,
        """\
        server, powered_by = (
            request.headers['server'],
            request.headers['x-powered-by'],
        )
        """,
    )


def test_subscript_simple_double_quotes():
    check_transformed(
        """\
        request.META["HTTP_SERVER"]
        """,
        """\
        request.headers["server"]
        """,
    )


def test_subscript_two_words():
    check_transformed(
        """\
        request.META['HTTP_ACCEPT_ENCODING']
        """,
        """\
        request.headers['accept-encoding']
        """,
    )


def test_subscript_three_words():
    check_transformed(
        """\
        request.META['HTTP_X_POWERED_BY']
        """,
        """\
        request.headers['x-powered-by']
        """,
    )


def test_subscript_self_request():
    check_transformed(
        """\
        self.request.META['HTTP_ACCEPT_ENCODING']
        """,
        """\
        self.request.headers['accept-encoding']
        """,
    )


def test_get_simple():
    check_transformed(
        """\
        request.META.get('HTTP_SERVER')
        """,
        """\
        request.headers.get('server')
        """,
    )


def test_get_content_length():
    check_transformed(
        """\
        request.META.get('CONTENT_LENGTH')
        """,
        """\
        request.headers.get('content-length')
        """,
    )


def test_get_content_type():
    check_transformed(
        """\
        request.META.get('CONTENT_TYPE')
        """,
        """\
        request.headers.get('content-type')
        """,
    )


def test_get_default():
    check_transformed(
        """\
        request.META.get('HTTP_SERVER', '')
        """,
        """\
        request.headers.get('server', '')
        """,
    )


def test_get_self_request():
    check_transformed(
        """\
        request.META.get('HTTP_SERVER')
        """,
        """\
        request.headers.get('server')
        """,
    )


def test_in():
    check_transformed(
        """\
        'HTTP_AUTHORIZATION' in request.META
        """,
        """\
        'authorization' in request.headers
        """,
    )


def test_in_double_quotes():
    check_transformed(
        """\
        "HTTP_AUTHORIZATION" in request.META
        """,
        """\
        "authorization" in request.headers
        """,
    )


def test_in_within_if():
    check_transformed(
        """\
        if 'HTTP_AUTHORIZATION' in request.META:
            print('hi')
        """,
        """\
        if 'authorization' in request.headers:
            print('hi')
        """,
    )


def test_in_get_combined():
    check_transformed(
        """\
        if 'HTTP_AUTHORIZATION' in request.META:
            print(request.META.get('HTTP_AUTHORIZATION'))
        """,
        """\
        if 'authorization' in request.headers:
            print(request.headers.get('authorization'))
        """,
    )


def test_in_double_statement():
    check_transformed(
        """\
        if 'HTTP_AUTHORIZATION' in request.META and 'HTTP_SERVER' in request.META:
            print('hi')
        """,
        """\
        if 'authorization' in request.headers and 'server' in request.headers:
            print('hi')
        """,
    )


def test_not_in():
    check_transformed(
        """\
        'HTTP_SERVER' not in request.META
        """,
        """\
        'server' not in request.headers
        """,
    )


def test_not_in_within_if():
    check_transformed(
        """\
        if 'HTTP_AUTHORIZATION' not in request.META:
            print('hi')
        """,
        """\
        if 'authorization' not in request.headers:
            print('hi')
        """,
    )


def test_not_in_get_combined():
    check_transformed(
        """\
        if 'HTTP_AUTHORIZATION' not in request.META:
            print(request.META.get('HTTP_AUTHORIZATION'))
        """,
        """\
        if 'authorization' not in request.headers:
            print(request.headers.get('authorization'))
        """,
    )


def test_not_in_double_statement():
    check_transformed(
        """\
        if 'HTTP_AUTHORIZATION' not in request.META and \
              'HTTP_SERVER' not in request.META:
            print('hi')
        """,
        """\
        if 'authorization' not in request.headers and \
              'server' not in request.headers:
            print('hi')
        """,
    )

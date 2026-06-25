from __future__ import annotations

from functools import partial

from django_upgrade.data import Settings
from tests.fixers import tools

settings = Settings(target_version=(2, 0))
check_noop = partial(tools.check_noop, settings=settings)
check_transformed = partial(tools.check_transformed, settings=settings)


# Not imported from django.shortcuts


def test_not_imported():
    check_noop(
        """\
        def my_view(request):
            return render_to_response("t.html")
        """,
    )


def test_wrong_module():
    check_noop(
        """\
        from myapp.shortcuts import render_to_response

        def my_view(request):
            return render_to_response("t.html")
        """,
    )


def test_aliased_import():
    check_noop(
        """\
        from django.shortcuts import render_to_response as rtr

        def my_view(request):
            return rtr("t.html")
        """,
    )


# Version guard


def test_older_version():
    check_noop(
        """\
        from django.shortcuts import render_to_response

        def my_view(request):
            return render_to_response("t.html")
        """,
        settings=Settings(target_version=(1, 11)),
    )


# Calls outside a function with 'request' as first arg


def test_call_outside_any_function():
    check_noop(
        """\
        from django.shortcuts import render_to_response

        response = render_to_response("t.html")
        """,
    )


def test_call_in_function_without_request_arg():
    check_noop(
        """\
        from django.shortcuts import render_to_response

        def helper(ctx):
            return render_to_response("t.html", ctx)
        """,
    )


def test_call_in_function_request_not_first_arg():
    check_noop(
        """\
        from django.shortcuts import render_to_response

        def my_view(arg, request):
            return render_to_response("t.html")
        """,
    )


def test_mixed_rewritable_and_not():
    """When some calls cannot be rewritten, leave the import alone too."""
    check_noop(
        """\
        from django.shortcuts import render_to_response

        def my_view(request):
            return render_to_response("t.html")

        def helper(ctx):
            return render_to_response("t.html", ctx)
        """,
    )


def test_nested_function_inner_shadows_request():
    """Inner function without request blocks rewrite of outer call too."""
    check_noop(
        """\
        from django.shortcuts import render_to_response

        def my_view(request):
            def inner(other):
                return render_to_response("t.html")
            return render_to_response("t.html")
        """,
    )


def test_lambda_with_render_to_response():
    check_noop(
        """\
        from django.shortcuts import render_to_response

        fn = lambda request: render_to_response("t.html")
        """,
    )


def test_no_args():
    check_noop(
        """\
        from django.shortcuts import render_to_response

        def my_view(request):
            return render_to_response()
        """,
    )


def test_star_args():
    check_noop(
        """\
        from django.shortcuts import render_to_response

        def my_view(request):
            return render_to_response(*args)
        """,
    )


def test_double_star_kwargs():
    check_noop(
        """\
        from django.shortcuts import render_to_response

        def my_view(request):
            return render_to_response("t.html", **ctx)
        """,
    )


# render already imported


def test_render_already_imported():
    check_transformed(
        """\
        from django.shortcuts import render, render_to_response

        def my_view(request):
            return render_to_response("t.html")
        """,
        """\
        from django.shortcuts import render

        def my_view(request):
            return render(request, "t.html")
        """,
    )


# Successful transformations


def test_simple():
    check_transformed(
        """\
        from django.shortcuts import render_to_response

        def my_view(request):
            return render_to_response("t.html")
        """,
        """\
        from django.shortcuts import render

        def my_view(request):
            return render(request, "t.html")
        """,
    )


def test_with_context():
    check_transformed(
        """\
        from django.shortcuts import render_to_response

        def my_view(request):
            return render_to_response("t.html", {"key": "value"})
        """,
        """\
        from django.shortcuts import render

        def my_view(request):
            return render(request, "t.html", {"key": "value"})
        """,
    )


def test_with_keyword_args():
    check_transformed(
        """\
        from django.shortcuts import render_to_response

        def my_view(request):
            return render_to_response("t.html", context={"key": "value"})
        """,
        """\
        from django.shortcuts import render

        def my_view(request):
            return render(request, "t.html", context={"key": "value"})
        """,
    )


def test_with_status():
    check_transformed(
        """\
        from django.shortcuts import render_to_response

        def my_view(request):
            return render_to_response("t.html", status=404)
        """,
        """\
        from django.shortcuts import render

        def my_view(request):
            return render(request, "t.html", status=404)
        """,
    )


def test_async_view():
    check_transformed(
        """\
        from django.shortcuts import render_to_response

        async def my_view(request):
            return render_to_response("t.html")
        """,
        """\
        from django.shortcuts import render

        async def my_view(request):
            return render(request, "t.html")
        """,
    )


def test_import_with_other_names():
    check_transformed(
        """\
        from django.shortcuts import get_object_or_404, render_to_response

        def my_view(request):
            return render_to_response("t.html")
        """,
        """\
        from django.shortcuts import get_object_or_404, render

        def my_view(request):
            return render(request, "t.html")
        """,
    )


def test_multiple_views():
    check_transformed(
        """\
        from django.shortcuts import render_to_response

        def view_a(request):
            return render_to_response("a.html")

        def view_b(request):
            return render_to_response("b.html")
        """,
        """\
        from django.shortcuts import render

        def view_a(request):
            return render(request, "a.html")

        def view_b(request):
            return render(request, "b.html")
        """,
    )


def test_nested_function():
    """Call in inner function where the inner function has request as first arg."""
    check_transformed(
        """\
        from django.shortcuts import render_to_response

        def outer():
            def inner(request):
                return render_to_response("t.html")
        """,
        """\
        from django.shortcuts import render

        def outer():
            def inner(request):
                return render(request, "t.html")
        """,
    )

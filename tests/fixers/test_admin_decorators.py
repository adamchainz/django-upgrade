from __future__ import annotations

from django_upgrade.data import Settings
from tests.fixers.tools import check_noop, check_transformed

settings = Settings(target_version=(3, 1))


def test_unknown_attribute():
    check_noop(
        """\
        def make_published(request, queryset):
            pass

        make_published.long_description = "yada"
        """,
        settings,
    )


def test_module_action_description():
    check_transformed(
        """\
        def make_published(request, queryset):
            pass

        make_published.short_description = 'yada'
        """,
        """\
        from django.contrib import admin

        @admin.action(
            description='yada',
        )
        def make_published(request, queryset):
            pass
        """,
        settings,
    )


# def test_class_action_description():
#     check_transformed(
#         """\
#         class MyModelAdmin:
#             def make_published(self, request, queryset):
#                 pass

#             make_published.short_description = 'yada'
#         """,
#         """\
#         from django.contrib import admin

#         @admin.action(
#             description='yada',
#         )
#         def make_published(request, queryset):
#             pass
#         """,
#         settings,
#     )


# def test_function_action_description():
#     check_transformed(
#         """\
#         def outer():
#             print('making action')

#             def make_published(request, queryset):
#                 pass

#             make_published.short_description = 'yada'

#             return make_published
#         """,
#         """\
#         def outer():
#             print('making action')

#             from django.contrib import admin

#             @admin.action(
#                 description='yada',
#             )
#             def make_published(request, queryset):
#                 pass
#         """,
#         settings,
#     )


# def test_module_action_description_multiline():
#     check_transformed(
#         """\
#         def make_published(request, queryset):
#             pass

#         make_published.short_description = (
#             'yada'
#             'yada!'
#         )
#         """,
#         """\
#         from django.contrib import admin

#         @admin.action(
#             description=(
#                 'yada'
#                 'yada!'
#             ),
#         )
#         def make_published(request, queryset):
#             pass
#         """,
#         settings,
#     )

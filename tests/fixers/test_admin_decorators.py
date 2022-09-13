from __future__ import annotations

from django_upgrade.data import Settings
from tests.fixers.tools import check_noop, check_transformed

settings = Settings(target_version=(3, 2))


def test_module_action_unknown_attribute():
    check_noop(
        """\
        from django.contrib import admin

        def make_published(modeladmin, request, queryset):
            pass

        make_published.long_description = "yada"
        """,
        settings,
    )


def test_module_action_incorrect_argument_count():
    check_noop(
        """\
        from django.contrib import admin

        def make_published(request):
            pass

        make_published.long_description = "yada"
        """,
        settings,
    )


def test_module_action_kwargs():
    check_noop(
        """\
        from django.contrib import admin

        def make_published(modeladmin, request, queryset, *, extra=True):
            pass

        make_published.long_description = "yada"
        """,
        settings,
    )


def test_module_action_admin_not_imported():
    check_noop(
        """\
        def make_published(modeladmin, request, queryset):
            pass

        make_published.short_description = 'yada'
        """,
        settings,
    )


def test_module_action_admin_imported_with_as():
    check_noop(
        """\
        from django.contrib import admin as shmadmin

        def make_published(modeladmin, request, queryset):
            pass

        make_published.long_description = "yada"
        """,
        settings,
    )


def test_module_action_admin_using_setattr():
    check_noop(
        """\
        from django.contrib import admin

        def make_published(modeladmin, request, queryset):
            pass

        setattr(make_published, "long_description", "yada")
        """,
        settings,
    )


def test_module_action_description():
    check_transformed(
        """\
        from django.contrib import admin

        def make_published(modeladmin, request, queryset):
            pass

        make_published.short_description = 'yada'
        """,
        """\
        from django.contrib import admin

        @admin.action(
            description='yada',
        )
        def make_published(modeladmin, request, queryset):
            pass

        """,
        settings,
    )


def test_module_action_pos_only_args():
    check_transformed(
        """\
        from django.contrib import admin

        def make_published(modeladmin, request, queryset, /):
            pass

        make_published.short_description = 'yada'
        """,
        """\
        from django.contrib import admin

        @admin.action(
            description='yada',
        )
        def make_published(modeladmin, request, queryset, /):
            pass

        """,
        settings,
    )


def test_module_action_permissions():
    check_transformed(
        """\
        from django.contrib import admin

        def make_published(modeladmin, request, queryset):
            pass

        make_published.allowed_permissions = ('change',)
        """,
        """\
        from django.contrib import admin

        @admin.action(
            permissions=('change',),
        )
        def make_published(modeladmin, request, queryset):
            pass

        """,
        settings,
    )


def test_module_action_both():
    check_transformed(
        """\
        from django.contrib import admin

        def make_published(modeladmin, request, queryset):
            pass

        make_published.allowed_permissions = ('change',)
        make_published.short_description = 'yada'
        """,
        """\
        from django.contrib import admin

        @admin.action(
            description='yada',
            permissions=('change',),
        )
        def make_published(modeladmin, request, queryset):
            pass

        """,
        settings,
    )


def test_module_action_description_multiline():
    # We don't really care about parenthesizing this nicely, just that it's
    # valid syntax
    check_transformed(
        """\
        from django.contrib import admin

        def make_published(modeladmin, request, queryset):
            pass

        make_published.short_description = (
            'yada'
            'yada!'
        )
        """,
        """\
        from django.contrib import admin

        @admin.action(
            description='yada'
                'yada!',
        )
        def make_published(modeladmin, request, queryset):
            pass

        """,
        settings,
    )


def test_module_action_comment_not_copied():
    # Mypy complains about setting the func attribute, but not about the
    # decorator, so it seems wise to ensure comments aren't copied.
    check_transformed(
        """\
        from django.contrib import admin

        def make_published(modeladmin, request, queryset):
            pass

        make_published.short_description = 'yada'  # type: ignore [attr-defined]
        """,
        """\
        from django.contrib import admin

        @admin.action(
            description='yada',
        )
        def make_published(modeladmin, request, queryset):
            pass

        """,
        settings,
    )


def test_class_action_unknown_attribute():
    check_noop(
        """\
        from django.contrib import admin

        class BookAdmin(admin.ModelAdmin):
            def make_published(modeladmin, request, queryset):
                pass

            make_published.long_description = "yada"
        """,
        settings,
    )


def test_class_action_description():
    check_transformed(
        """\
        from django.contrib import admin

        class BookAdmin(admin.ModelAdmin):
            def make_published(self, request, queryset):
                pass

            make_published.short_description = "yada"
        """,
        """\
        from django.contrib import admin

        class BookAdmin(admin.ModelAdmin):
            @admin.action(
                description="yada",
            )
            def make_published(self, request, queryset):
                pass

        """,
        settings,
    )


def test_class_action_permissions():
    check_transformed(
        """\
        from django.contrib import admin

        class BookAdmin(admin.ModelAdmin):
            def make_published(self, request, queryset):
                pass

            make_published.allowed_permissions = ('change',)
        """,
        """\
        from django.contrib import admin

        class BookAdmin(admin.ModelAdmin):
            @admin.action(
                permissions=('change',),
            )
            def make_published(self, request, queryset):
                pass

        """,
        settings,
    )


def test_class_action_both():
    check_transformed(
        """\
        from django.contrib import admin

        class BookAdmin(admin.ModelAdmin):
            def make_published(self, request, queryset):
                pass

            make_published.allowed_permissions = ('change',)
            make_published.short_description = 'yada'
        """,
        """\
        from django.contrib import admin

        class BookAdmin(admin.ModelAdmin):
            @admin.action(
                description='yada',
                permissions=('change',),
            )
            def make_published(self, request, queryset):
                pass

        """,
        settings,
    )

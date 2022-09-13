from __future__ import annotations

from django_upgrade.data import Settings
from tests.fixers.tools import check_noop, check_transformed

settings = Settings(target_version=(3, 2))


class TestActionFunctions:
    def test_module_unknown_attribute(self):
        check_noop(
            """\
            from django.contrib import admin

            def make_published(modeladmin, request, queryset):
                ...

            make_published.long_description = "yada"
            """,
            settings,
        )

    def test_module_incorrect_argument_count(self):
        check_noop(
            """\
            from django.contrib import admin

            def make_published(request):
                ...

            make_published.short_description = "yada"
            """,
            settings,
        )

    def test_module_kwargs(self):
        check_noop(
            """\
            from django.contrib import admin

            def make_published(modeladmin, request, queryset, *, extra=True):
                ...

            make_published.short_description = "yada"
            """,
            settings,
        )

    def test_module_admin_not_imported(self):
        check_noop(
            """\
            def make_published(modeladmin, request, queryset):
                ...

            make_published.short_description = 'yada'
            """,
            settings,
        )

    def test_module_admin_imported_with_as(self):
        check_noop(
            """\
            from django.contrib import admin as shmadmin

            def make_published(modeladmin, request, queryset):
                ...

            make_published.long_description = "yada"
            """,
            settings,
        )

    def test_module_admin_using_setattr(self):
        check_noop(
            """\
            from django.contrib import admin

            def make_published(modeladmin, request, queryset):
                ...

            setattr(make_published, "long_description", "yada")
            """,
            settings,
        )

    def test_module_description(self):
        check_transformed(
            """\
            from django.contrib import admin

            def make_published(modeladmin, request, queryset):
                ...

            make_published.short_description = 'yada'
            """,
            """\
            from django.contrib import admin

            @admin.action(
                description='yada',
            )
            def make_published(modeladmin, request, queryset):
                ...

            """,
            settings,
        )

    def test_module_pos_only_args(self):
        check_transformed(
            """\
            from django.contrib import admin

            def make_published(modeladmin, request, queryset, /):
                ...

            make_published.short_description = 'yada'
            """,
            """\
            from django.contrib import admin

            @admin.action(
                description='yada',
            )
            def make_published(modeladmin, request, queryset, /):
                ...

            """,
            settings,
        )

    def test_module_permissions(self):
        check_transformed(
            """\
            from django.contrib import admin

            def make_published(modeladmin, request, queryset):
                ...

            make_published.allowed_permissions = ('change',)
            """,
            """\
            from django.contrib import admin

            @admin.action(
                permissions=('change',),
            )
            def make_published(modeladmin, request, queryset):
                ...

            """,
            settings,
        )

    def test_module_both(self):
        check_transformed(
            """\
            from django.contrib import admin

            def make_published(modeladmin, request, queryset):
                ...

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
                ...

            """,
            settings,
        )

    def test_module_description_multiline(self):
        # We don't really care about parenthesizing this nicely, just that it's
        # valid syntax
        check_transformed(
            """\
            from django.contrib import admin

            def make_published(modeladmin, request, queryset):
                ...

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
                ...

            """,
            settings,
        )

    def test_module_comment_not_copied(self):
        # Mypy complains about setting the func attribute, but not about the
        # decorator, so it seems wise to ensure comments aren't copied.
        check_transformed(
            """\
            from django.contrib import admin

            def make_published(modeladmin, request, queryset):
                ...

            make_published.short_description = 'yada'  # type: ignore [attr-defined]
            """,
            """\
            from django.contrib import admin

            @admin.action(
                description='yada',
            )
            def make_published(modeladmin, request, queryset):
                ...

            """,
            settings,
        )

    def test_class_unknown_attribute(self):
        check_noop(
            """\
            from django.contrib import admin

            class BookAdmin(admin.ModelAdmin):
                def make_published(modeladmin, request, queryset):
                    ...

                make_published.long_description = "yada"
            """,
            settings,
        )

    def test_class_description(self):
        check_transformed(
            """\
            from django.contrib import admin

            class BookAdmin(admin.ModelAdmin):
                def make_published(self, request, queryset):
                    ...

                make_published.short_description = "yada"
            """,
            """\
            from django.contrib import admin

            class BookAdmin(admin.ModelAdmin):
                @admin.action(
                    description="yada",
                )
                def make_published(self, request, queryset):
                    ...

            """,
            settings,
        )

    def test_class_permissions(self):
        check_transformed(
            """\
            from django.contrib import admin

            class BookAdmin(admin.ModelAdmin):
                def make_published(self, request, queryset):
                    ...

                make_published.allowed_permissions = ('change',)
            """,
            """\
            from django.contrib import admin

            class BookAdmin(admin.ModelAdmin):
                @admin.action(
                    permissions=('change',),
                )
                def make_published(self, request, queryset):
                    ...

            """,
            settings,
        )

    def test_class_both(self):
        check_transformed(
            """\
            from django.contrib import admin

            class BookAdmin(admin.ModelAdmin):
                def make_published(self, request, queryset):
                    ...

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
                    ...

            """,
            settings,
        )

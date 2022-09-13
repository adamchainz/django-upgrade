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


class TestDisplayFunctions:
    def test_module_unknown_attribute(self):
        check_noop(
            """\
            from django.contrib import admin

            def upper_case_name(obj):
                ...

            upper_case_name.long_description = "yada"
            """,
            settings,
        )

    def test_module_incorrect_argument_count(self):
        check_noop(
            """\
            from django.contrib import admin

            def upper_case_name(obj, obj2):
                ...

            upper_case_name.short_description = "yada"
            """,
            settings,
        )

    def test_module_kwargs(self):
        check_noop(
            """\
            from django.contrib import admin

            def upper_case_name(obj, *, proper=True):
                ...

            upper_case_name.short_description = "yada"
            """,
            settings,
        )

    def test_module_admin_not_imported(self):
        check_noop(
            """\
            def upper_case_name(obj):
                ...

            upper_case_name.short_description = 'yada'
            """,
            settings,
        )

    def test_module_admin_imported_with_as(self):
        check_noop(
            """\
            from django.contrib import admin as shmadmin

            def upper_case_name(obj):
                ...

            upper_case_name.short_description = "yada"
            """,
            settings,
        )

    def test_module_admin_using_setattr(self):
        check_noop(
            """\
            from django.contrib import admin

            def upper_case_name(obj):
                ...

            setattr(upper_case_name, "short_description", "yada")
            """,
            settings,
        )

    def test_module_description(self):
        check_transformed(
            """\
            from django.contrib import admin

            def upper_case_name(obj):
                ...

            upper_case_name.short_description = 'yada'
            """,
            """\
            from django.contrib import admin

            @admin.display(
                description='yada',
            )
            def upper_case_name(obj):
                ...

            """,
            settings,
        )

    def test_module_boolean(self):
        check_transformed(
            """\
            from django.contrib import admin

            def upper_case_name(obj):
                ...

            upper_case_name.boolean = True
            """,
            """\
            from django.contrib import admin

            @admin.display(
                boolean=True,
            )
            def upper_case_name(obj):
                ...

            """,
            settings,
        )

    def test_module_empty_value(self):
        check_transformed(
            """\
            from django.contrib import admin

            def upper_case_name(obj):
                ...

            upper_case_name.empty_value_display = "xxx"
            """,
            """\
            from django.contrib import admin

            @admin.display(
                empty_value="xxx",
            )
            def upper_case_name(obj):
                ...

            """,
            settings,
        )

    def test_module_ordering(self):
        check_transformed(
            """\
            from django.contrib import admin

            def upper_case_name(obj):
                ...

            upper_case_name.admin_order_field = "name"
            """,
            """\
            from django.contrib import admin

            @admin.display(
                ordering="name",
            )
            def upper_case_name(obj):
                ...

            """,
            settings,
        )

    def test_module_all(self):
        # boolean and empty_value are mutually exclusive but we don't check
        # that here, let it crash at runtime
        check_transformed(
            """\
            from django.contrib import admin

            def upper_case_name(obj):
                ...

            upper_case_name.empty_value_display = "xxx"
            upper_case_name.short_description = 'yada'
            upper_case_name.admin_order_field = "name"
            upper_case_name.boolean = True
            """,
            """\
            from django.contrib import admin

            @admin.display(
                description='yada',
                boolean=True,
                empty_value="xxx",
                ordering="name",
            )
            def upper_case_name(obj):
                ...

            """,
            settings,
        )

    def test_class_unknown_attribute(self):
        check_noop(
            """\
            from django.contrib import admin

            class BookAdmin(admin.ModelAdmin):
                def is_published(self. obj):
                    ...

                is_published.long_description = "yada"
            """,
            settings,
        )

    def test_class_description(self):
        check_transformed(
            """\
            from django.contrib import admin

            @admin.register(Book)
            class BookAdmin(admin.ModelAdmin):
                def is_published(self, obj):
                    ...

                is_published.short_description = 'yada'
            """,
            """\
            from django.contrib import admin

            @admin.register(Book)
            class BookAdmin(admin.ModelAdmin):
                @admin.display(
                    description='yada',
                )
                def is_published(self, obj):
                    ...

            """,
            settings,
        )

    def test_class_boolean(self):
        check_transformed(
            """\
            from django.contrib import admin

            @admin.register(Book)
            class BookAdmin(admin.ModelAdmin):
                def is_published(self, obj):
                    ...

                is_published.boolean = True
            """,
            """\
            from django.contrib import admin

            @admin.register(Book)
            class BookAdmin(admin.ModelAdmin):
                @admin.display(
                    boolean=True,
                )
                def is_published(self, obj):
                    ...

            """,
            settings,
        )

    def test_class_empty_value(self):
        check_transformed(
            """\
            from django.contrib import admin

            @admin.register(Book)
            class BookAdmin(admin.ModelAdmin):
                def is_published(self, obj):
                    ...

                is_published.empty_value_display = "xxx"
            """,
            """\
            from django.contrib import admin

            @admin.register(Book)
            class BookAdmin(admin.ModelAdmin):
                @admin.display(
                    empty_value="xxx",
                )
                def is_published(self, obj):
                    ...

            """,
            settings,
        )

    def test_class_ordering(self):
        check_transformed(
            """\
            from django.contrib import admin

            @admin.register(Book)
            class BookAdmin(admin.ModelAdmin):
                def is_published(self, obj):
                    ...

                is_published.admin_order_field = "-publish_date"
            """,
            """\
            from django.contrib import admin

            @admin.register(Book)
            class BookAdmin(admin.ModelAdmin):
                @admin.display(
                    ordering="-publish_date",
                )
                def is_published(self, obj):
                    ...

            """,
            settings,
        )

    def test_class_many(self):
        check_transformed(
            """\
            from django.contrib import admin

            @admin.register(Book)
            class BookAdmin(admin.ModelAdmin):
                def is_published(self, obj):
                    ...

                is_published.boolean = True
                is_published.admin_order_field = '-publish_date'
                is_published.short_description = 'Is Published?'
            """,
            """\
            from django.contrib import admin

            @admin.register(Book)
            class BookAdmin(admin.ModelAdmin):
                @admin.display(
                    description='Is Published?',
                    boolean=True,
                    ordering='-publish_date',
                )
                def is_published(self, obj):
                    ...

            """,
            settings,
        )

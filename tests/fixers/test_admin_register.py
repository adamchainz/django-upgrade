from __future__ import annotations

from django_upgrade.data import Settings
from tests.fixers.tools import check_noop, check_transformed

settings = Settings(target_version=(1, 7))


def test_no_custom_admin_class():
    check_noop(
        """\
        from django.contrib import admin
        from myapp.models import Author

        admin.site.register(Author)
        """,
        settings,
    )


def test_kwargs_not_supported():
    # To support this we would have to update the admin class definition
    # by overriding attributes values. Django emulate that behaviour by
    # constructing a subclass with these attributes.
    check_noop(
        """\
        from django.contrib import admin
        from myapp.models import Author

        class AuthorAdmin(admin.ModelAdmin):
            pass
        admin.site.register(Author, AuthorAdmin, save_as=True)
        """,
        settings,
    )


def test_imported_custom_admin():
    check_noop(
        """\
        from django.contrib import admin
        from myapp.models import Author
        from myapp.admin import AuthorAdmin

        admin.site.register(Author, AuthorAdmin)
        """,
        settings,
    )


def test_already_using_decorator_registration():
    check_noop(
        """\
        from django.contrib import admin
        from myapp.models import Author

        @admin.register(Author)
        class AuthorAdmin(admin.ModelAdmin):
            pass
        """,
        settings,
    )


def test_multiple_model_one_admin():
    check_noop(
        """\
        from django.contrib import admin
        from myapp.models import MyModel1, MyModel2

        class MyCustomAdmin:
            pass

        admin.site.register(MyModel1, MyCustomAdmin)
        admin.site.register(MyModel2, MyCustomAdmin)
        """,
        settings,
    )


def test_py2_style_init_super():
    check_noop(
        """\
        from django.contrib import admin
        from myapp.models import Author

        class AuthorAdmin(admin.ModelAdmin):
            def __init__(self, *args, **kwargs):
                super(AuthorAdmin, self).__init__(*args, **kwargs)

            def other(self):
                pass

        admin.site.register(Author, AuthorAdmin)
        """,
        settings=settings,
    )


def test_py2_style_init_super_with_inheritance():
    check_noop(
        """\
        from django.contrib import admin
        from myapp.models import Author

        class AuthorAdmin(CustomMixin):
            def __init__(self, *args, **kwargs):
                super(CustomMixin, self).__init__(*args, **kwargs)

        admin.site.register(Author, AuthorAdmin)
        """,
        settings=settings,
    )


def test_py2_style_init_super_with_outer_branching():
    check_noop(
        """\
        from django.contrib import admin
        from myapp.models import Author

        class AuthorAdmin(CustomMixin):
            if something():
                def __init__(self, *args, **kwargs):
                    super(CustomMixin, self).__init__(*args, **kwargs)

        admin.site.register(Author, AuthorAdmin)
        """,
        settings=settings,
    )


def test_py2_style_init_super_delayed():
    check_noop(
        """\
        from django.contrib import admin
        from myapp.models import Author

        class AuthorAdmin(CustomMixin):
            def __init__(self, *args, **kwargs):
                sup = super(CustomMixin, self)
                sup.__init__(*args, **kwargs)

        admin.site.register(Author, AuthorAdmin)
        """,
        settings=settings,
    )


def test_py2_style_init_super_with_inner_branching():
    check_transformed(
        """\
        import sys
        from django.contrib import admin
        from myapp.models import Ham, Spam

        class HamAdmin(...):
            pass

        class SpamAdmin(SubAdmin):
            def __init__(self, *args, **kwargs):
                if sys.version_info >= (3, 10):
                    # something
                    super(SpamAdmin, self).__init__(*args, **kwargs)
                else:
                    # something else
                    super(SubAdmin, self).__init__(*args, **kwargs)

        admin.site.register(Ham, HamAdmin)
        admin.site.register(Spam, SpamAdmin)
        """,
        """\
        import sys
        from django.contrib import admin
        from myapp.models import Ham, Spam

        @admin.register(Ham)
        class HamAdmin(...):
            pass

        class SpamAdmin(SubAdmin):
            def __init__(self, *args, **kwargs):
                if sys.version_info >= (3, 10):
                    # something
                    super(SpamAdmin, self).__init__(*args, **kwargs)
                else:
                    # something else
                    super(SubAdmin, self).__init__(*args, **kwargs)

        admin.site.register(Spam, SpamAdmin)
        """,
        settings=settings,
    )


def test_py3_style_init_super():
    check_transformed(
        """\
        from django.contrib import admin
        from myapp.models import Author

        class AuthorAdmin(CustomMixin):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)

        admin.site.register(Author, AuthorAdmin)
        """,
        """\
        from django.contrib import admin
        from myapp.models import Author

        @admin.register(Author)
        class AuthorAdmin(CustomMixin):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)

        """,
        settings=settings,
    )


def test_py2_style_new_super():
    check_noop(
        """\
        from django.contrib import admin
        from myapp.models import Author

        class AuthorAdmin(admin.ModelAdmin):
            def __new__(cls, *args, **kwargs):
                super(AuthorAdmin, self).__new__(cls, *args, **kwargs)

        admin.site.register(Author, AuthorAdmin)
        """,
        settings=settings,
    )


def test_simple_rewrite():
    check_transformed(
        """\
        from django.contrib import admin
        from myapp.models import Author

        class AuthorAdmin(admin.ModelAdmin):
            pass
        admin.site.register(Author, AuthorAdmin)
        """,
        """\
        from django.contrib import admin
        from myapp.models import Author

        @admin.register(Author)
        class AuthorAdmin(admin.ModelAdmin):
            pass
        """,
        settings=settings,
    )


def test_multiple_rewrite():
    check_transformed(
        """\
        from django.contrib import admin
        from myapp.models import Author, Blog

        class AuthorAdmin(admin.ModelAdmin):
            pass

        class BlogAdmin(admin.ModelAdmin):
            pass

        admin.site.register(Blog, BlogAdmin)
        admin.site.register(Author, AuthorAdmin)
        """,
        """\
        from django.contrib import admin
        from myapp.models import Author, Blog

        @admin.register(Author)
        class AuthorAdmin(admin.ModelAdmin):
            pass

        @admin.register(Blog)
        class BlogAdmin(admin.ModelAdmin):
            pass

        """,
        settings=settings,
    )


def test_custom_model_admin_base_class():
    check_transformed(
        """\
        from django.contrib import admin
        from myapp.models import Author
        from myapp.admin import CustomModelAdmin

        class AuthorAdmin(CustomModelAdmin):
            pass
        admin.site.register(Author, AuthorAdmin)
        """,
        """\
        from django.contrib import admin
        from myapp.models import Author
        from myapp.admin import CustomModelAdmin

        @admin.register(Author)
        class AuthorAdmin(CustomModelAdmin):
            pass
        """,
        settings=settings,
    )


def test_complete():
    check_transformed(
        """\
        from django.contrib import admin
        from myapp.models import Author, Blog, MyModel1, MyModel2
        from myapp.admin import MyImportedAdmin

        class MyCustomAdmin:
            pass

        class AuthorAdmin(CustomModelAdmin):
            pass

        admin.site.register(MyModel1, MyCustomAdmin)
        admin.site.register(MyModel2, MyCustomAdmin)
        admin.site.register(Author, AuthorAdmin)
        admin.site.register(Blog, MyImportedAdmin)
        """,
        """\
        from django.contrib import admin
        from myapp.models import Author, Blog, MyModel1, MyModel2
        from myapp.admin import MyImportedAdmin

        class MyCustomAdmin:
            pass

        @admin.register(Author)
        class AuthorAdmin(CustomModelAdmin):
            pass

        admin.site.register(MyModel1, MyCustomAdmin)
        admin.site.register(MyModel2, MyCustomAdmin)
        admin.site.register(Blog, MyImportedAdmin)
        """,
        settings=settings,
    )

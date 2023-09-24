from __future__ import annotations

import sys

import pytest

from django_upgrade.data import Settings
from tests.fixers.tools import check_noop
from tests.fixers.tools import check_transformed

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


def test_register_different_parent():
    check_noop(
        """\
        from django.contrib import admin
        from myapp.models import Author

        class AuthorAdmin(admin.ModelAdmin):
            ...

        if True:
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


def test_rewrite():
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


def test_rewrite_gis():
    check_transformed(
        """\
        from django.contrib.gis import admin
        from myapp.models import Author

        class AuthorAdmin(admin.ModelAdmin):
            pass
        admin.site.register(Author, AuthorAdmin)
        """,
        """\
        from django.contrib.gis import admin
        from myapp.models import Author

        @admin.register(Author)
        class AuthorAdmin(admin.ModelAdmin):
            pass
        """,
        settings=settings,
    )


def test_rewrite_indented():
    check_transformed(
        """\
        from django.contrib import admin
        from myapp.models import Author

        if True:
            class AuthorAdmin(admin.ModelAdmin):
                pass
            admin.site.register(Author, AuthorAdmin)
        """,
        """\
        from django.contrib import admin
        from myapp.models import Author

        if True:
            @admin.register(Author)
            class AuthorAdmin(admin.ModelAdmin):
                pass
        """,
        settings=settings,
    )


def test_rewrite_kwarg():
    check_transformed(
        """\
        from django.contrib import admin
        from myapp.models import Author

        class AuthorAdmin(admin.ModelAdmin):
            pass
        admin.site.register(Author, admin_class=AuthorAdmin)
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


def test_rewrite_class_decorator():
    check_transformed(
        """\
        from django.contrib import admin
        from myapp.admin_tools import add_display_methods
        from myapp.models import Author

        @add_display_methods
        class AuthorAdmin(admin.ModelAdmin):
            pass
        admin.site.register(Author, admin_class=AuthorAdmin)
        """,
        """\
        from django.contrib import admin
        from myapp.admin_tools import add_display_methods
        from myapp.models import Author

        @admin.register(Author)
        @add_display_methods
        class AuthorAdmin(admin.ModelAdmin):
            pass
        """,
        settings=settings,
    )


def test_rewrite_class_decorator_multiple():
    check_transformed(
        """\
        from django.contrib import admin
        from myapp.admin_tools import add_common_actions, add_display_methods
        from myapp.models import Author

        @add_common_actions
        @add_display_methods
        class AuthorAdmin(admin.ModelAdmin):
            pass
        admin.site.register(Author, admin_class=AuthorAdmin)
        """,
        """\
        from django.contrib import admin
        from myapp.admin_tools import add_common_actions, add_display_methods
        from myapp.models import Author

        @admin.register(Author)
        @add_common_actions
        @add_display_methods
        class AuthorAdmin(admin.ModelAdmin):
            pass
        """,
        settings=settings,
    )


@pytest.mark.skipif(sys.version_info < (3, 9), reason="Python 3.9+ PEP 614 decorators")
def test_rewrite_class_decorator_multiline():
    check_transformed(
        """\
        from django.contrib import admin
        from myapp.admin_tools import add_display_methods
        from myapp.models import Author

        @(
            add_display_methods
        )
        class AuthorAdmin(admin.ModelAdmin):
            pass
        admin.site.register(Author, admin_class=AuthorAdmin)
        """,
        """\
        from django.contrib import admin
        from myapp.admin_tools import add_display_methods
        from myapp.models import Author

        @admin.register(Author)
        @(
            add_display_methods
        )
        class AuthorAdmin(admin.ModelAdmin):
            pass
        """,
        settings=settings,
    )


def test_rewrite_comment():
    check_transformed(
        """\
        from django.contrib import admin
        from myapp.models import Author

        class AuthorAdmin(admin.ModelAdmin):
            pass
        admin.site.register(Author, AuthorAdmin)  # yada
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


def test_py2_style_init_inside_async_function():
    check_transformed(
        """\
        from django.contrib import admin
        from myapp.models import Author

        class AuthorAdmin(admin.ModelAdmin):
            async def whatever():
                def __init__(self, *args, **kwargs):
                    super(AuthorAdmin, self).__init__(*args, **kwargs)

        admin.site.register(Author, AuthorAdmin)
        """,
        """\
        from django.contrib import admin
        from myapp.models import Author

        @admin.register(Author)
        class AuthorAdmin(admin.ModelAdmin):
            async def whatever():
                def __init__(self, *args, **kwargs):
                    super(AuthorAdmin, self).__init__(*args, **kwargs)

        """,
        settings=settings,
    )


def test_py2_style_init_inside_inner_class():
    check_transformed(
        """\
        from django.contrib import admin
        from myapp.models import Author

        class AuthorAdmin(admin.ModelAdmin):
            class Inner:
                def __init__(self, *args, **kwargs):
                    super(AuthorAdmin, self).__init__(*args, **kwargs)

        admin.site.register(Author, AuthorAdmin)
        """,
        """\
        from django.contrib import admin
        from myapp.models import Author

        @admin.register(Author)
        class AuthorAdmin(admin.ModelAdmin):
            class Inner:
                def __init__(self, *args, **kwargs):
                    super(AuthorAdmin, self).__init__(*args, **kwargs)

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


def test_multiple_model_multiline_registration():
    check_transformed(
        """\
        from django.contrib import admin
        from myapp.models import MyModel1, MyModel2

        class MyCustomAdmin:
            pass

        admin.site.register(MyModel1, MyCustomAdmin)
        admin.site.register(MyModel2, MyCustomAdmin)
        """,
        """\
        from django.contrib import admin
        from myapp.models import MyModel1, MyModel2

        @admin.register(MyModel1, MyModel2)
        class MyCustomAdmin:
            pass

        """,
        settings=settings,
    )


def test_multiple_model_multiline_registration_sorted():
    check_transformed(
        """\
        from django.contrib import admin
        from myapp.models import MyModel1, MyModel2

        class MyCustomAdmin:
            pass

        admin.site.register(MyModel2, MyCustomAdmin)
        admin.site.register(MyModel1, MyCustomAdmin)
        """,
        """\
        from django.contrib import admin
        from myapp.models import MyModel1, MyModel2

        @admin.register(MyModel1, MyModel2)
        class MyCustomAdmin:
            pass

        """,
        settings=settings,
    )


def test_multiple_model_tuple_registration():
    check_transformed(
        """\
        from django.contrib import admin
        from myapp.models import MyModel1, MyModel2

        class MyCustomAdmin:
            pass

        admin.site.register((MyModel1, MyModel2), MyCustomAdmin)
        """,
        """\
        from django.contrib import admin
        from myapp.models import MyModel1, MyModel2

        @admin.register(MyModel1, MyModel2)
        class MyCustomAdmin:
            pass

        """,
        settings=settings,
    )


def test_multiple_model_list_registration():
    check_transformed(
        """\
        from django.contrib import admin
        from myapp.models import MyModel1, MyModel2

        class MyCustomAdmin:
            pass

        admin.site.register([MyModel1, MyModel2], MyCustomAdmin)
        """,
        """\
        from django.contrib import admin
        from myapp.models import MyModel1, MyModel2

        @admin.register(MyModel1, MyModel2)
        class MyCustomAdmin:
            pass

        """,
        settings=settings,
    )


def test_multiple_model_registration_with_kwarg():
    check_transformed(
        """\
        from django.contrib import admin
        from myapp.models import MyModel1, MyModel2

        class MyCustomAdmin:
            pass

        admin.site.register([MyModel1, MyModel2], admin_class=MyCustomAdmin)
        """,
        """\
        from django.contrib import admin
        from myapp.models import MyModel1, MyModel2

        @admin.register(MyModel1, MyModel2)
        class MyCustomAdmin:
            pass

        """,
        settings=settings,
    )


def test_multiple_model_mixed_registration():
    check_transformed(
        """\
        from django.contrib import admin
        from myapp.models import MyModel1, MyModel2, MyModel3, MyModel4

        class MyCustomAdmin:
            pass

        admin.site.register((MyModel1, MyModel2), MyCustomAdmin)
        admin.site.register(MyModel3, MyCustomAdmin)
        admin.site.register([MyModel4], MyCustomAdmin)
        """,
        """\
        from django.contrib import admin
        from myapp.models import MyModel1, MyModel2, MyModel3, MyModel4

        @admin.register(MyModel1, MyModel2, MyModel3, MyModel4)
        class MyCustomAdmin:
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

        @admin.register(MyModel1, MyModel2)
        class MyCustomAdmin:
            pass

        @admin.register(Author)
        class AuthorAdmin(CustomModelAdmin):
            pass

        admin.site.register(Blog, MyImportedAdmin)
        """,
        settings=settings,
    )


def test_custom_admin_not_an_admin_file():
    check_noop(
        """\
        from myapp.admin import MyModel, CustomModelAdmin, custom_site
        from django.contrib import admin

        class MyModelAdmin(CustomModelAdmin):
            pass

        custom_site.register(MyModel, MyModelAdmin)
        """,
        settings,
        filename="a_d_m_i_n.py",
    )


def test_custom_admin_not_an_admin_model():
    check_noop(
        """\
        from myapp.admin import MyModel, CustomModel, custom_site
        from django.contrib import admin

        class Custom(MyModel):
            pass

        custom_site.register(MyModel, Custom)
        """,
        settings,
        filename="admin.py",
    )


def test_custom_admin_doesnt_end_with_site():
    check_noop(
        """\
        from myapp.admin import MyModel, CustomModelAdmin, app
        from django.contrib import admin

        class MyModelAdmin(CustomModelAdmin):
            pass

        app.register(MyModel, MyModelAdmin)
        """,
        settings,
        filename="admin.py",
    )


def test_custom_admin_site_defined_after_admin():
    check_noop(
        """\
        from django.contrib import admin

        class MyModelAdmin(admin.ModelAdmin):
            pass

        custom_site = admin.AdminSite(...)

        custom_site.register(MyModel, MyModelAdmin)
        """,
        settings=settings,
        filename="admin.py",
    )


def test_custom_admin_site_defined_after_admin_import():
    check_noop(
        """\
        from django.contrib import admin

        class MyModelAdmin(admin.ModelAdmin):
            pass

        from myapp.admin import custom_site

        custom_site.register(MyModel, MyModelAdmin)
        """,
        settings=settings,
        filename="admin.py",
    )


def test_custom_admin_site_defined_after_admin_import_as():
    check_noop(
        """\
        from django.contrib import admin

        class MyModelAdmin(admin.ModelAdmin):
            pass

        from myapp.admin import site as custom_site

        custom_site.register(MyModel, MyModelAdmin)
        """,
        settings=settings,
        filename="admin.py",
    )


def test_custom_admin_site():
    check_transformed(
        """\
        from myapp.admin import custom_site, CustomModelAdmin
        from django.contrib import admin

        class MyModelAdmin(CustomModelAdmin):
            pass

        custom_site.register(MyModel, MyModelAdmin)
        """,
        """\
        from myapp.admin import custom_site, CustomModelAdmin
        from django.contrib import admin

        @admin.register(MyModel, site=custom_site)
        class MyModelAdmin(CustomModelAdmin):
            pass

        """,
        settings=settings,
        filename="admin.py",
    )


def test_multiple_admin_sites():
    check_transformed(
        """\
        from myapp.admin import custom_site
        from django.contrib import admin

        class MyModelAdmin(admin.ModelAdmin):
            pass

        custom_site.register(MyModel, MyModelAdmin)
        admin.site.register(MyModel, MyModelAdmin)
        """,
        """\
        from myapp.admin import custom_site
        from django.contrib import admin

        @admin.register(MyModel)
        @admin.register(MyModel, site=custom_site)
        class MyModelAdmin(admin.ModelAdmin):
            pass

        """,
        settings=settings,
        filename="admin.py",
    )


def test_multiple_admin_sites_not_admin_file():
    check_transformed(
        """\
        from myapp.admin import custom_site
        from django.contrib import admin

        class MyModelAdmin(admin.ModelAdmin):
            pass

        custom_site.register(MyModel, MyModelAdmin)
        admin.site.register(MyModel, MyModelAdmin)
        """,
        """\
        from myapp.admin import custom_site
        from django.contrib import admin

        @admin.register(MyModel)
        class MyModelAdmin(admin.ModelAdmin):
            pass

        custom_site.register(MyModel, MyModelAdmin)
        """,
        settings=settings,
        filename="a_d_m_i_n.py",
    )


def test_multiple_admin_sites_sorted():
    check_transformed(
        """\
        from myapp.admin import custom_site, secret_site
        from django.contrib import admin

        class MyModelAdmin(admin.ModelAdmin):
            pass

        admin.site.register(MyModel, MyModelAdmin)
        custom_site.register(MyModel, MyModelAdmin)
        secret_site.register(MyModel, MyModelAdmin)
        """,
        """\
        from myapp.admin import custom_site, secret_site
        from django.contrib import admin

        @admin.register(MyModel)
        @admin.register(MyModel, site=custom_site)
        @admin.register(MyModel, site=secret_site)
        class MyModelAdmin(admin.ModelAdmin):
            pass

        """,
        settings=settings,
        filename="admin.py",
    )


def test_unregister():
    check_noop(
        """\
        from django.contrib import admin
        from myapp.models import MyModel1

        class MyCustomAdmin:
            pass

        admin.site.unregister(MyModel1)
        admin.site.register(MyModel1, MyCustomAdmin)
        """,
        settings=settings,
        filename="admin.py",
    )


def test_unregister_reoccurring():
    check_noop(
        """\
        from django.contrib import admin
        from myapp.models import MyModel1

        class MyCustomAdmin:
            pass

        admin.site.unregister(MyModel1)
        admin.site.register(MyModel1, MyCustomAdmin)
        admin.site.unregister(MyModel1)
        admin.site.register(MyModel1, MyCustomAdmin)
        """,
        settings=settings,
        filename="admin.py",
    )


def test_unregister_no_effect_if_register_precedes():
    check_transformed(
        """\
        from django.contrib import admin
        from myapp.models import MyModel1

        class MyCustomAdmin:
            pass

        admin.site.register(MyModel1, MyCustomAdmin)
        admin.site.unregister(MyModel1)
        """,
        """\
        from django.contrib import admin
        from myapp.models import MyModel1

        @admin.register(MyModel1)
        class MyCustomAdmin:
            pass

        admin.site.unregister(MyModel1)
        """,
        settings=settings,
        filename="admin.py",
    )


def test_unregister_at_least_one_model_leaves_register():
    check_noop(
        """\
        from django.contrib import admin
        from myapp.models import MyModel1, MyModel2

        class MyCustomAdmin:
            pass

        admin.site.unregister([MyModel1])
        admin.site.register([MyModel1, MyModel2], MyCustomAdmin)
        """,
        settings=settings,
        filename="admin.py",
    )


def test_unregister_kwarg():
    check_noop(
        """\
        from django.contrib import admin
        from myapp.models import MyModel1, MyModel2

        class MyCustomAdmin:
            pass

        admin.site.unregister(model_or_iterable=MyModel1)
        admin.site.register([MyModel1, MyModel2], MyCustomAdmin)
        """,
        settings=settings,
        filename="admin.py",
    )


def test_unregister_undetectable_names():
    check_noop(
        """\
        from django.contrib import admin
        from myapp.models import MyModel1, MyModel2

        class MyCustomAdmin:
            pass

        admin.site.unregister(*some_models())
        admin.site.register([MyModel1, MyModel2], MyCustomAdmin)
        """,
        settings=settings,
        filename="admin.py",
    )


def test_unregister_undetectable_names_and_more():
    check_noop(
        """\
        from django.contrib import admin
        from myapp.models import MyModel1, MyModel2

        class MyCustomAdmin:
            pass

        admin.site.unregister(*some_models())
        admin.site.unregister(MyModel2)
        admin.site.register(MyModel1, MyCustomAdmin)
        """,
        settings=settings,
        filename="admin.py",
    )


def test_unregister_multiple_admins():
    check_noop(
        """\
        from django.contrib import admin
        from myapp.models import MyModel1, MyModel2

        class MyCustomAdmin:
            pass

        admin.site.unregister(MyModel1)
        admin.site.register(MyModel1, MyCustomAdmin)

        class MyOtherCustomAdmin:
            pass

        admin.site.register(MyModel1, MyOtherCustomAdmin)
        """,
        settings=settings,
        filename="admin.py",
    )


def test_unregister_multiple_admins_different_models():
    check_transformed(
        """\
        from django.contrib import admin
        from myapp.models import MyModel1, MyModel2

        class MyCustomAdmin:
            pass

        admin.site.unregister(MyModel1)
        admin.site.register(MyModel1, MyCustomAdmin)

        class MyOtherCustomAdmin:
            pass

        admin.site.register(MyModel2, MyOtherCustomAdmin)
        """,
        """\
        from django.contrib import admin
        from myapp.models import MyModel1, MyModel2

        class MyCustomAdmin:
            pass

        admin.site.unregister(MyModel1)
        admin.site.register(MyModel1, MyCustomAdmin)

        @admin.register(MyModel2)
        class MyOtherCustomAdmin:
            pass

        """,
        settings=settings,
        filename="admin.py",
    )


def test_unregister_multiple_models_for_model_admin():
    check_transformed(
        """\
        from django.contrib import admin
        from myapp.models import MyModel1, MyModel2, MyModel3, MyModel4

        class MyCustomAdmin:
            pass

        admin.site.unregister([MyModel1, MyModel2])
        admin.site.register((MyModel1, MyModel2), MyCustomAdmin)
        admin.site.register(MyModel3, MyCustomAdmin)
        admin.site.register([MyModel4], MyCustomAdmin)
        """,
        """\
        from django.contrib import admin
        from myapp.models import MyModel1, MyModel2, MyModel3, MyModel4

        @admin.register(MyModel3, MyModel4)
        class MyCustomAdmin:
            pass

        admin.site.unregister([MyModel1, MyModel2])
        admin.site.register((MyModel1, MyModel2), MyCustomAdmin)
        """,
        settings=settings,
        filename="admin.py",
    )


def test_unregister_custom_admin_unregister():
    check_transformed(
        """\
        from myapp.admin import custom_site, secret_site
        from django.contrib import admin

        class MyModelAdmin(admin.ModelAdmin):
            pass

        admin.site.register(MyModel, MyModelAdmin)
        custom_site.unregister([MyModel])
        custom_site.register(MyModel, MyModelAdmin)
        secret_site.register(MyModel, MyModelAdmin)
        """,
        """\
        from myapp.admin import custom_site, secret_site
        from django.contrib import admin

        @admin.register(MyModel)
        @admin.register(MyModel, site=secret_site)
        class MyModelAdmin(admin.ModelAdmin):
            pass

        custom_site.unregister([MyModel])
        custom_site.register(MyModel, MyModelAdmin)
        """,
        settings=settings,
        filename="admin.py",
    )


def test_unregister_not_admin_file():
    check_transformed(
        """\
        from myapp.admin import custom_site, secret_site
        from django.contrib import admin

        class MyModelAdmin(admin.ModelAdmin):
            pass

        admin.site.register(MyModel, MyModelAdmin)
        custom_site.unregister(MyModel)
        custom_site.register(MyModel, MyModelAdmin)
        secret_site.register(MyModel, MyModelAdmin)
        """,
        """\
        from myapp.admin import custom_site, secret_site
        from django.contrib import admin

        @admin.register(MyModel)
        class MyModelAdmin(admin.ModelAdmin):
            pass

        custom_site.unregister(MyModel)
        custom_site.register(MyModel, MyModelAdmin)
        secret_site.register(MyModel, MyModelAdmin)
        """,
        settings=settings,
        filename="a_d_m_i_n.py",
    )

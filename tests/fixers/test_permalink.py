from __future__ import annotations

from functools import partial

from django_upgrade.data import Settings
from tests.fixers import tools

settings = Settings(target_version=(1, 11))
check_noop = partial(tools.check_noop, settings=settings)
check_transformed = partial(tools.check_transformed, settings=settings)


# noop cases


def test_wrong_module():
    check_noop(
        """\
        from myapp.db import models


        class MyModel(models.Model):
            @models.permalink
            def url(self):
                return ("view_name", [self.pk])
        """,
    )


def test_older_version():
    check_noop(
        """\
        from django.db import models


        class MyModel(models.Model):
            @models.permalink
            def url(self):
                return ("view_name", [self.pk])
        """,
        settings=Settings(target_version=(1, 10)),
    )


def test_multiple_decorators():
    check_noop(
        """\
        from django.db import models


        class MyModel(models.Model):
            @some_other_decorator
            @models.permalink
            def url(self):
                return ("view_name", [self.pk])
        """,
    )


def test_multiple_statements():
    check_noop(
        """\
        from django.db import models


        class MyModel(models.Model):
            @models.permalink
            def url(self):
                x = 1
                return ("view_name", [self.pk])
        """,
    )


def test_no_return_value():
    check_noop(
        """\
        from django.db import models


        class MyModel(models.Model):
            @models.permalink
            def url(self):
                pass
        """,
    )


def test_return_not_tuple():
    check_noop(
        """\
        from django.db import models


        class MyModel(models.Model):
            @models.permalink
            def url(self):
                return "view_name"
        """,
    )


def test_return_tuple_too_short():
    check_noop(
        """\
        from django.db import models


        class MyModel(models.Model):
            @models.permalink
            def url(self):
                return ("view_name",)
        """,
    )


def test_return_tuple_too_long():
    check_noop(
        """\
        from django.db import models


        class MyModel(models.Model):
            @models.permalink
            def url(self):
                return ("view_name", [self.pk], {}, "extra")
        """,
    )


# transforms


def test_basic():
    check_transformed(
        """\
        from django.db import models


        class MyModel(models.Model):
            @models.permalink
            def url(self):
                return ("guitarist_detail", [self.slug])
        """,
        """\
        from django.db import models
        from django.urls import reverse


        class MyModel(models.Model):
            def url(self):
                return reverse("guitarist_detail", args=[self.slug])
        """,
    )


def test_with_kwargs():
    check_transformed(
        """\
        from django.db import models


        class MyModel(models.Model):
            @models.permalink
            def url(self):
                return ("guitarist_detail", [self.slug], {"extra": 1})
        """,
        """\
        from django.db import models
        from django.urls import reverse


        class MyModel(models.Model):
            def url(self):
                return reverse("guitarist_detail", args=[self.slug], kwargs={"extra": 1})
        """,
    )


def test_decorator_with_trailing_comment():
    check_transformed(
        """\
        from django.db import models


        class MyModel(models.Model):
            @models.permalink  # noqa
            def url(self):
                return ("guitarist_detail", [self.slug])
        """,
        """\
        from django.db import models
        from django.urls import reverse


        class MyModel(models.Model):
            def url(self):
                return reverse("guitarist_detail", args=[self.slug])
        """,
    )


def test_return_bare_tuple():
    check_transformed(
        """\
        from django.db import models


        class MyModel(models.Model):
            @models.permalink
            def url(self):
                return "guitarist_detail", [self.slug]
        """,
        """\
        from django.db import models
        from django.urls import reverse


        class MyModel(models.Model):
            def url(self):
                return reverse("guitarist_detail", args=[self.slug])
        """,
    )


def test_return_bare_tuple_with_kwargs():
    check_transformed(
        """\
        from django.db import models


        class MyModel(models.Model):
            @models.permalink
            def url(self):
                return "guitarist_detail", [], {"extra": 1}
        """,
        """\
        from django.db import models
        from django.urls import reverse


        class MyModel(models.Model):
            def url(self):
                return reverse("guitarist_detail", args=[], kwargs={"extra": 1})
        """,
    )


def test_no_args():
    check_transformed(
        """\
        from django.db import models


        class MyModel(models.Model):
            @models.permalink
            def url(self):
                return ("guitarist_detail", [])
        """,
        """\
        from django.db import models
        from django.urls import reverse


        class MyModel(models.Model):
            def url(self):
                return reverse("guitarist_detail", args=[])
        """,
    )


def test_reverse_already_imported():
    check_transformed(
        """\
        from django.db import models
        from django.urls import reverse


        class MyModel(models.Model):
            @models.permalink
            def url(self):
                return ("guitarist_detail", [self.slug])
        """,
        """\
        from django.db import models
        from django.urls import reverse


        class MyModel(models.Model):
            def url(self):
                return reverse("guitarist_detail", args=[self.slug])
        """,
    )

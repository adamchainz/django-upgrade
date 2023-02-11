from __future__ import annotations

from django_upgrade.data import Settings
from tests.fixers.tools import check_noop
from tests.fixers.tools import check_transformed


class TestUtilsFunctional:
    settings = Settings(target_version=(3, 1))

    def test_unmatched_import(self):
        check_noop(
            """\
            from functools import lru_cache
            """,
            self.settings,
        )

    def test_unmatched_import_name(self):
        check_noop(
            """\
            from django.utils.functional import SimpleLazyObject
            """,
            self.settings,
        )

    def test_unrecognized_import_format(self):
        check_noop(
            """\
            from django.utils import functional

            @functional.lru_cache
            def foo():
                ...
            """,
            self.settings,
        )

    def test_fixed(self):
        check_transformed(
            """\
            from django.utils.functional import lru_cache

            @lru_cache
            def foo():
                ...
            """,
            """\
            from functools import lru_cache

            @lru_cache
            def foo():
                ...
            """,
            self.settings,
        )


class TestJsonField:
    settings = Settings(target_version=(3, 1))

    def test_no_deprecated_alias(self):
        check_noop(
            """\
            from django.contrib.postgres.fields import IntegerRangeField
            """,
            self.settings,
        )

    def test_old_target_version(self):
        check_noop(
            """\
            from django.contrib.postgres.fields import JSONField
            """,
            Settings(target_version=(3, 0)),
        )

    def test_unrecognized_import_format(self):
        check_noop(
            """\
            from django.contrib.postgres import fields

            fields.JSONField()
            """,
            self.settings,
        )

    def test_untransformed_in_migration_file(self):
        check_noop(
            """\
            from django.contrib.postgres.fields import (
                JSONField, KeyTransform,  KeyTextTransform,
            )
            """,
            self.settings,
            filename="example/core/migrations/0001_initial.py",
        )

    def test_full(self):
        check_transformed(
            """\
            from django.contrib.postgres.fields import (
                JSONField, KeyTransform,  KeyTextTransform,
            )
            """,
            """\
            from django.db.models import JSONField
            from django.db.models.fields.json import KeyTextTransform, KeyTransform
            """,
            self.settings,
        )

    def test_model_field(self):
        check_transformed(
            """\
            from django.contrib.postgres.fields import JSONField
            """,
            """\
            from django.db.models import JSONField
            """,
            self.settings,
        )

    def test_model_field_indented(self):
        check_transformed(
            """\
            def f(self):
                from django.contrib.postgres.fields import JSONField, bla
            """,
            """\
            def f(self):
                from django.db.models import JSONField
                from django.contrib.postgres.fields import bla
            """,
            self.settings,
        )

    def test_model_field_submodule(self):
        check_transformed(
            """\
            from django.contrib.postgres.fields.jsonb import JSONField
            """,
            """\
            from django.db.models import JSONField
            """,
            self.settings,
        )

    def test_form_field(self):
        check_transformed(
            """\
            from django.contrib.postgres.forms import JSONField
            """,
            """\
            from django.forms import JSONField
            """,
            self.settings,
        )

    def test_form_field_submodule(self):
        check_transformed(
            """\
            from django.contrib.postgres.forms.jsonb import JSONField
            """,
            """\
            from django.forms import JSONField
            """,
            self.settings,
        )

    def test_transforms(self):
        check_transformed(
            """\
            from django.contrib.postgres.fields import KeyTextTransform
            yada = 1
            from django.contrib.postgres.fields.jsonb import KeyTransform
            """,
            """\
            from django.db.models.fields.json import KeyTextTransform
            yada = 1
            from django.db.models.fields.json import KeyTransform
            """,
            self.settings,
        )


class TestCompatibility109:
    settings = Settings(target_version=(1, 9))

    def test_unmatched_import(self):
        check_noop(
            """\
            from example import pretty_name
            pretty_name()
            """,
            self.settings,
        )

    def test_unmatched_name(self):
        check_noop(
            """\
            from django.forms.forms import something
            """,
            self.settings,
        )

    def test_unrecognized_import_format(self):
        check_noop(
            """\
            from django.forms import forms

            forms.pretty_name()
            """,
            self.settings,
        )

    def test_import_star(self):
        check_transformed(
            """\
            from django.forms.forms import *

            pretty_name()
            """,
            """\
            from django.forms.forms import *

            pretty_name()
            """,
            self.settings,
        )

    def test_name_imported(self):
        check_transformed(
            """\
            from django.forms.forms import pretty_name

            pretty_name()
            """,
            """\
            from django.forms.utils import pretty_name

            pretty_name()
            """,
            self.settings,
        )

    def test_name_imported_as_other_name(self):
        check_transformed(
            """\
            from django.forms.forms import pretty_name as pn

            pn()
            """,
            """\
            from django.forms.utils import pretty_name as pn

            pn()
            """,
            self.settings,
        )


class TestCompatibility111:
    settings = Settings(target_version=(1, 11))

    def test_unmatched_import(self):
        check_noop(
            """\
            from example import EmptyResultSet
            EmptyResultSet()
            """,
            self.settings,
        )

    def test_unmatched_import_name(self):
        check_noop(
            """\
            from django.db.models.fields import something
            """,
            self.settings,
        )

    def test_unrecognized_import_format(self):
        check_noop(
            """\
            from django.db.models import query

            query.EmptyResultSet()
            """,
            self.settings,
        )

    def test_exception_class_imported(self):
        check_transformed(
            """\
            from django.db.models.fields import FieldDoesNotExist
            from django.db.models.query import EmptyResultSet
            from django.db.models.sql.datastructures import EmptyResultSet
            from django.db.models.sql import EmptyResultSet

            EmptyResultSet()
            """,
            """\
            from django.core.exceptions import FieldDoesNotExist
            from django.core.exceptions import EmptyResultSet
            from django.core.exceptions import EmptyResultSet
            from django.core.exceptions import EmptyResultSet

            EmptyResultSet()
            """,
            self.settings,
        )

    def test_exception_class_imported_as_other_name(self):
        check_transformed(
            """\
            from django.db.models.query import EmptyResultSet as EmptyResultSetExc

            EmptyResultSetExc()
            """,
            """\
            from django.core.exceptions import EmptyResultSet as EmptyResultSetExc

            EmptyResultSetExc()
            """,
            self.settings,
        )


def test_all_transformed():
    check_transformed(
        """\
        from django.forms.forms import pretty_name
        from django.forms.forms import BoundField
        from django.db.models.fields import FieldDoesNotExist
        from django.db.models.query import EmptyResultSet
        from django.db.models.sql import EmptyResultSet
        from django.db.models.sql.datastructures import EmptyResultSet
        from django.utils.functional import lru_cache
        from django.contrib.postgres.forms import JSONField
        from django.contrib.postgres.forms.jsonb import JSONField
        """,
        """\
        from django.forms.utils import pretty_name
        from django.forms.boundfield import BoundField
        from django.core.exceptions import FieldDoesNotExist
        from django.core.exceptions import EmptyResultSet
        from django.core.exceptions import EmptyResultSet
        from django.core.exceptions import EmptyResultSet
        from functools import lru_cache
        from django.forms import JSONField
        from django.forms import JSONField
        """,
        Settings(target_version=(3, 1)),
    )

from __future__ import annotations

from functools import partial

from django_upgrade.data import Settings
from tests.fixers import tools

settings = Settings(target_version=(4, 0))
check_noop = partial(tools.check_noop, settings=settings)
check_transformed = partial(tools.check_transformed, settings=settings)


def test_no_deprecated_alias():
    check_noop(
        """\
        from django.contrib.gis.admin.options import GeoAdmin

        GeoAdmin
        """,
    )


def test_aliased_import():
    check_noop(
        """\
        from django.contrib.gis.admin.options import OSMGeoAdmin as GeoAdmin

        class MyModelAdmin(GeoAdmin):
            pass
        """,
    )


def test_no_class_usage():
    check_noop(
        """\
        from django.contrib.gis.admin.options import OSMGeoAdmin
        """,
    )


def test_other_reference():
    check_noop(
        """\
        from django.contrib.gis.admin.options import OSMGeoAdmin

        x = OSMGeoAdmin
        """,
    )


def test_other_reference_alongside_valid_class():
    check_noop(
        """\
        from django.contrib.gis.admin.options import OSMGeoAdmin

        class MyModelAdmin(OSMGeoAdmin):
            pass

        x = OSMGeoAdmin
        """,
    )


def test_non_name_base():
    check_noop(
        """\
        from django.contrib.gis.admin.options import OSMGeoAdmin

        class MyModelAdmin(module.OSMGeoAdmin):
            pass
        """,
    )


def test_no_bases():
    check_noop(
        """\
        from django.contrib.gis.admin.options import OSMGeoAdmin

        class MyModelAdmin():
            pass
        """,
    )


def test_keyword_argument():
    check_noop(
        """\
        from django.contrib.gis.admin.options import OSMGeoAdmin

        class MyModelAdmin(OSMGeoAdmin, metaclass=Meta):
            pass
        """,
    )


def test_multiple_bases():
    check_noop(
        """\
        from django.contrib.gis.admin.options import OSMGeoAdmin

        class MyModelAdmin(OSMGeoAdmin, other):
            pass
        """,
    )


def test_not_a_top_level_import():
    check_noop(
        """\
        if True:
            from django.contrib.gis.admin.options import OSMGeoAdmin

        class MyModelAdmin(OSMGeoAdmin):
            pass
        """,
    )


def test_overloaded_attribute():
    check_noop(
        """\
        from django.contrib.gis.admin.options import OSMGeoAdmin

        class MyModelAdmin(OSMGeoAdmin):
            default_lon = 1
        """,
    )


def test_overloaded_attribute_annotated():
    check_noop(
        """\
        from django.contrib.gis.admin.options import OSMGeoAdmin

        class MyModelAdmin(OSMGeoAdmin):
            default_lon: int = 1
        """,
    )


def test_overloaded_attribute_augmented():
    check_noop(
        """\
        from django.contrib.gis.admin.options import OSMGeoAdmin

        class MyModelAdmin(OSMGeoAdmin):
            default_lon += 1
        """,
    )


def test_overloaded_attribute_annotated_non_name_target():
    check_transformed(
        """\
        from django.contrib.gis.admin.options import OSMGeoAdmin

        class MyModelAdmin(OSMGeoAdmin):
            self.default_lon: int = 1
        """,
        """\
        from django.contrib.gis.admin.options import GISModelAdmin

        class MyModelAdmin(GISModelAdmin):
            self.default_lon: int = 1
        """,
    )


def test_overloaded_attribute_non_name_target():
    check_transformed(
        """\
        from django.contrib.gis.admin.options import OSMGeoAdmin

        class MyModelAdmin(OSMGeoAdmin):
            self.default_lon = 1
        """,
        """\
        from django.contrib.gis.admin.options import GISModelAdmin

        class MyModelAdmin(GISModelAdmin):
            self.default_lon = 1
        """,
    )


def test_osm_geo_admin_plain():
    check_transformed(
        """\
        from django.contrib.gis.admin.options import OSMGeoAdmin

        class MyModelAdmin(OSMGeoAdmin):
            pass
        """,
        """\
        from django.contrib.gis.admin.options import GISModelAdmin

        class MyModelAdmin(GISModelAdmin):
            pass
        """,
    )


def test_geo_model_admin_plain():
    check_transformed(
        """\
        from django.contrib.gis.admin.options import GeoModelAdmin

        class MyModelAdmin(GeoModelAdmin):
            pass
        """,
        """\
        from django.contrib.gis.admin.options import GISModelAdmin

        class MyModelAdmin(GISModelAdmin):
            pass
        """,
    )

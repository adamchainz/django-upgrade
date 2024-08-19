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


def test_osm_geo_admin_multiple_inheritance():
    check_noop(
        """\
        from django.contrib.gis.admin.options import OSMGeoAdmin

        class MyModelAdmin(OSMGeoAdmin, other):
            pass
        """,
    )


def test_osm_geo_admin_overloaded_attribute():
    check_noop(
        """\
        from django.contrib.gis.admin.options import OSMGeoAdmin

        class MyModelAdmin(OSMGeoAdmin):
            default_lon = 1
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


def test_osm_geo_admin_aliased():
    check_transformed(
        """\
        from django.contrib.gis.admin.options import OSMGeoAdmin as GeoAdmin

        class MyModelAdmin(GeoAdmin):
            pass
        """,
        """\
        from django.contrib.gis.admin.options import GISModelAdmin as GeoAdmin

        class MyModelAdmin(GeoAdmin):
            pass
        """,
    )


def test_geo_model_admin_aliased():
    check_transformed(
        """\
        from django.contrib.gis.admin.options import GeoModelAdmin as GeoAdmin

        class MyModelAdmin(GeoAdmin):
            pass
        """,
        """\
        from django.contrib.gis.admin.options import GISModelAdmin as GeoAdmin

        class MyModelAdmin(GeoAdmin):
            pass
        """,
    )

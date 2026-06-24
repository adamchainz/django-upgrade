"""
Migrate from deprecated GIS admin classes to the new ones:
https://docs.djangoproject.com/en/4.0/releases/4.0/#:~:text=The%20django%2Econtrib%2Egis%2Eadmin%2EGeoModelAdmin
"""

from __future__ import annotations

import ast
from collections.abc import Iterable
from functools import partial

from tokenize_rt import Offset

from django_upgrade.ast import ast_start_offset, is_rewritable_import_from
from django_upgrade.data import Fixer, State, TokenFunc
from django_upgrade.tokens import find_and_replace_name, update_import_names

fixer = Fixer(
    __name__,
    min_version=(4, 0),
)

MODULE = "django.contrib.gis.admin.options"
RENAMES = {
    "OSMGeoAdmin": "GISModelAdmin",
    "GeoModelAdmin": "GISModelAdmin",
}


@fixer.register(ast.ImportFrom)
def visit_ImportFrom(
    state: State,
    node: ast.ImportFrom,
    parents: tuple[ast.AST, ...],
) -> Iterable[tuple[Offset, TokenFunc]]:
    if node.module != MODULE or not is_rewritable_import_from(node):
        return

    if len(parents) > 1:  # not a top-level import
        return

    names_to_rename = {
        alias.name
        for alias in node.names
        if alias.name in RENAMES and alias.asname is None
    }
    if not names_to_rename:
        return

    module = parents[0]
    assert isinstance(module, ast.Module)

    name_map: dict[str, str] = {}
    valid_classes: list[tuple[str, ast.ClassDef]] = []

    for name in names_to_rename:
        classes, has_other_refs = _find_valid_classes(module, name)
        if not classes or has_other_refs:
            continue
        name_map[name] = RENAMES[name]
        valid_classes.extend((name, cls) for cls in classes)

    if not name_map:
        return

    yield (
        ast_start_offset(node),
        partial(update_import_names, node=node, name_map=name_map),
    )

    for name, cls in valid_classes:
        base = cls.bases[0]
        yield (
            ast_start_offset(base),
            partial(find_and_replace_name, name=name, new=RENAMES[name]),
        )


def _find_valid_classes(
    module: ast.Module, name: str
) -> tuple[list[ast.ClassDef], bool]:
    """
    Walk the module and return (valid_classes, has_other_refs) for `name`.

    valid_classes: ClassDef nodes whose sole base is `name` and which do not
    define any GeoModelAdmin-specific attributes.
    has_other_refs: True if `name` appears as an ast.Name anywhere other than
    as the sole base of a class in valid_classes.
    """
    valid_classes: list[ast.ClassDef] = []

    for node in ast.walk(module):
        if (
            isinstance(node, ast.ClassDef)
            and len(node.bases) == 1
            and not node.keywords
            and isinstance(node.bases[0], ast.Name)
            and node.bases[0].id == name
            and not _class_defines_bad_attr(node)
        ):
            valid_classes.append(node)

    valid_base_ids = {id(cls.bases[0]) for cls in valid_classes}
    has_other_refs = any(
        id(node) not in valid_base_ids
        for node in ast.walk(module)
        if isinstance(node, ast.Name) and node.id == name
    )
    return valid_classes, has_other_refs


# Attributes defined by GeoModelAdmin that would be broken by switching to
# GISModelAdmin, since GISModelAdmin does not support them.
GEO_MODEL_ADMIN_ATTRS = frozenset(
    (
        "debug",
        "default_lat",
        "default_lon",
        "default_zoom",
        "display_srid",
        "display_wkt",
        "extra_js",
        "layerswitcher",
        "map_height",
        "map_srid",
        "map_template",
        "map_width",
        "max_extent",
        "max_resolution",
        "max_zoom",
        "min_zoom",
        "modifiable",
        "mouse_position",
        "num_zoom",
        "openlayers_url",
        "point_zoom",
        "scale_text",
        "scrollable",
        "units",
        "widget",
        "wms_layer",
        "wms_name",
        "wms_options",
        "wms_url",
    )
)


def _class_defines_bad_attr(node: ast.ClassDef) -> bool:
    for stmt in node.body:
        if isinstance(stmt, ast.Assign):
            for target in stmt.targets:
                if isinstance(target, ast.Name) and target.id in GEO_MODEL_ADMIN_ATTRS:
                    return True
        elif isinstance(stmt, (ast.AnnAssign, ast.AugAssign)):
            target = stmt.target
            if isinstance(target, ast.Name) and target.id in GEO_MODEL_ADMIN_ATTRS:
                return True
    return False

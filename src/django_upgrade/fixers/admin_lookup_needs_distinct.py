"""
Rename django.contrib.admin.utils.lookup_needs_distinct to lookup_spawns_duplicates:
https://docs.djangoproject.com/en/4.0/releases/4.0/#miscellaneous
"""

from __future__ import annotations

import ast
from functools import partial
from typing import Iterable

from tokenize_rt import Offset

from django_upgrade.ast import ast_start_offset
from django_upgrade.ast import is_rewritable_import_from
from django_upgrade.data import Fixer
from django_upgrade.data import State
from django_upgrade.data import TokenFunc
from django_upgrade.tokens import find_and_replace_name
from django_upgrade.tokens import update_import_names

fixer = Fixer(
    __name__,
    min_version=(4, 0),
)

MODULE = "django.contrib.admin.utils"
RENAMES = {
    "lookup_needs_distinct": "lookup_spawns_duplicates",
}


@fixer.register(ast.ImportFrom)
def visit_ImportFrom(
    state: State,
    node: ast.ImportFrom,
    parents: tuple[ast.AST, ...],
) -> Iterable[tuple[Offset, TokenFunc]]:
    if node.module == MODULE and is_rewritable_import_from(node):
        name_map = {}
        for alias in node.names:
            if alias.name in RENAMES:
                name_map[alias.name] = RENAMES[alias.name]

        if name_map:
            yield ast_start_offset(node), partial(
                update_import_names,
                node=node,
                name_map=name_map,
            )


@fixer.register(ast.Name)
def visit_Name(
    state: State,
    node: ast.Name,
    parents: tuple[ast.AST, ...],
) -> Iterable[tuple[Offset, TokenFunc]]:
    if (name := node.id) in RENAMES and name in state.from_imports[MODULE]:
        new_name = RENAMES[name]
        yield ast_start_offset(node), partial(
            find_and_replace_name, name=name, new=new_name
        )

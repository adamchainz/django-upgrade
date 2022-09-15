"""
Replace FloatRangeField with DecimalRangeField:
https://docs.djangoproject.com/en/2.2/releases/2.2/#features-deprecated-in-2-2
"""
from __future__ import annotations

import ast
from functools import partial
from typing import Iterable

from tokenize_rt import Offset

from django_upgrade.ast import ast_start_offset, is_rewritable_import_from
from django_upgrade.data import Fixer, State, TokenFunc
from django_upgrade.tokens import find_and_replace_name, update_import_names

fixer = Fixer(
    __name__,
    min_version=(2, 2),
)

MODULES = {
    "django.contrib.postgres.fields",
    "django.contrib.postgres.fields.ranges",
    "django.contrib.postgres.forms",
    "django.contrib.postgres.forms.ranges",
}
NAME_MAP = {
    "FloatRangeField": "DecimalRangeField",
}


@fixer.register(ast.ImportFrom)
def visit_ImportFrom(
    state: State,
    node: ast.ImportFrom,
    parents: list[ast.AST],
) -> Iterable[tuple[Offset, TokenFunc]]:
    if (
        node.module in MODULES
        and is_rewritable_import_from(node)
        and any(alias.name in NAME_MAP for alias in node.names)
    ):
        yield ast_start_offset(node), partial(
            update_import_names, node=node, name_map=NAME_MAP
        )


@fixer.register(ast.Name)
def visit_Name(
    state: State,
    node: ast.Name,
    parents: list[ast.AST],
) -> Iterable[tuple[Offset, TokenFunc]]:
    if (name := node.id) in NAME_MAP and any(
        name in state.from_imports[m] for m in MODULES
    ):
        yield ast_start_offset(node), partial(
            find_and_replace_name, name=name, new=NAME_MAP[name]
        )

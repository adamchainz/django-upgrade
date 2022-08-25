"""
Replace django.utils.timezone.utc with datetime.timezone.utc
https://docs.djangoproject.com/en/4.1/releases/4.1/#id2
"""
from __future__ import annotations

import ast
from functools import partial
from typing import Iterable, MutableMapping
from weakref import WeakKeyDictionary

from tokenize_rt import Offset, Token

from django_upgrade.ast import ast_start_offset, is_rewritable_import_from
from django_upgrade.data import Fixer, State, TokenFunc
from django_upgrade.tokens import extract_indent, insert, replace, update_import_names

fixer = Fixer(
    __name__,
    min_version=(4, 1),
)

MODULE = "django.utils.timezone"


@fixer.register(ast.ImportFrom)
def visit_ImportFrom(
    state: State,
    node: ast.ImportFrom,
    parent: ast.AST,
) -> Iterable[tuple[Offset, TokenFunc]]:
    if (
        node.module == MODULE
        and is_rewritable_import_from(node)
        and any(alias.name == "utc" for alias in node.names)
    ):
        start = ast_start_offset(node)
        updating_import[state] = True
        yield start, partial(replace_import, node=node)


def replace_import(tokens: list[Token], i: int, *, node: ast.ImportFrom) -> None:
    j, indent = extract_indent(tokens, i)
    update_import_names(tokens, i, node=node, name_map={"utc": ""})
    insert(tokens, j, new_src=f"{indent}from datetime import timezone\n")


# Track if the import is being updated
updating_import: MutableMapping[State, bool] = WeakKeyDictionary()


@fixer.register(ast.Name)
def visit_Name(
    state: State,
    node: ast.Name,
    parent: ast.AST,
) -> Iterable[tuple[Offset, TokenFunc]]:
    if (
        updating_import.get(state, False)
        and node.id == "utc"
        and not isinstance(parent, ast.Attribute)
    ):
        yield ast_start_offset(node), partial(
            replace,
            src="timezone.utc",
        )

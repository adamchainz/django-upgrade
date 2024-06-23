"""
Add on_delete=models.CASCADE to ForeignKey and OneToOneField:
https://docs.djangoproject.com/en/stable/releases/1.9/#features-deprecated-in-1-9
"""

from __future__ import annotations

import ast
from functools import partial
from typing import Iterable
from typing import MutableMapping
from weakref import WeakKeyDictionary

from tokenize_rt import Offset
from tokenize_rt import Token

from django_upgrade.ast import ast_start_offset
from django_upgrade.ast import is_rewritable_import_from
from django_upgrade.data import Fixer
from django_upgrade.data import State
from django_upgrade.data import TokenFunc
from django_upgrade.tokens import OP
from django_upgrade.tokens import extract_indent
from django_upgrade.tokens import find
from django_upgrade.tokens import insert
from django_upgrade.tokens import parse_call_args

fixer = Fixer(
    __name__,
    min_version=(1, 9),
)


@fixer.register(ast.ImportFrom)
def visit_ImportFrom(
    state: State,
    node: ast.ImportFrom,
    parents: tuple[ast.AST, ...],
) -> Iterable[tuple[Offset, TokenFunc]]:
    if (
        node.module == "django.db.models"
        and is_rewritable_import_from(node)
        and any(alias.name in {"ForeignKey", "OneToOneField"} for alias in node.names)
    ):
        yield ast_start_offset(node), partial(
            update_django_models_import,
            node=node,
            state=state,
        )


# Track if we need to update `from django.db.models` import to add CASCADE.
should_update_import: MutableMapping[State, bool] = WeakKeyDictionary()


def update_django_models_import(
    tokens: list[Token], i: int, *, node: ast.ImportFrom, state: State
) -> None:
    if should_update_import.get(state, False):
        should_update_import[state] = False
        j, indent = extract_indent(tokens, i)
        insert(
            tokens,
            j,
            new_src=f"{indent}from django.db.models import CASCADE\n",
        )


@fixer.register(ast.Call)
def visit_Call(
    state: State,
    node: ast.Call,
    parents: tuple[ast.AST, ...],
) -> Iterable[tuple[Offset, TokenFunc]]:
    if (
        (
            (
                isinstance(node.func, ast.Attribute)
                and node.func.attr in {"ForeignKey", "OneToOneField"}
                and (models_imported := "models" in state.from_imports["django.db"])
                and isinstance(node.func.value, ast.Name)
                and node.func.value.id == "models"
            )
            or (
                isinstance(node.func, ast.Name)
                and node.func.id in {"ForeignKey", "OneToOneField"}
                and node.func.id in state.from_imports["django.db.models"]
                and (models_imported := False) is False  # force walrus
            )
        )
        and len(node.args) < 2
        and all(kw.arg != "on_delete" for kw in node.keywords)
    ):
        should_update_import[state] = not models_imported
        yield ast_start_offset(node), partial(
            add_on_delete_keyword,
            num_pos_args=len(node.args),
            models_imported=models_imported,
        )


def add_on_delete_keyword(
    tokens: list[Token], i: int, *, num_pos_args: int, models_imported: bool
) -> None:
    open_idx = find(tokens, i, name=OP, src="(")
    func_args, close_idx = parse_call_args(tokens, open_idx)

    if models_imported:
        new_src = "on_delete=models.CASCADE"
    else:
        new_src = "on_delete=CASCADE"

    if num_pos_args == 0:
        if len(func_args) > 0:
            new_src += ", "
        insert_idx = open_idx + 1
    else:
        pos_start_idx, pos_end_idx = func_args[num_pos_args - 1]
        insert_idx = pos_end_idx + 1

        if tokens[pos_end_idx].src == ")":
            insert_idx -= 1
            new_src = f", {new_src}"
        elif len(func_args) == 1:
            new_src = f" {new_src}"
        else:
            new_src = f" {new_src},"

    insert(tokens, insert_idx, new_src=new_src)

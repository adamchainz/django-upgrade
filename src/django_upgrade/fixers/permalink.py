"""
Rewrite @models.permalink decorator to use reverse():
https://docs.djangoproject.com/en/1.11/releases/1.11/#features-deprecated-in-1-11
"""

from __future__ import annotations

import ast
from collections.abc import Iterable, MutableMapping
from functools import partial
from weakref import WeakKeyDictionary

from tokenize_rt import UNIMPORTANT_WS, Offset, Token

from django_upgrade.ast import ast_start_offset, is_rewritable_import_from
from django_upgrade.data import Fixer, State, TokenFunc
from django_upgrade.tokens import (
    INDENT,
    NAME,
    OP,
    extract_indent,
    find,
    find_last_token,
    find_node,
    insert,
    parse_call_args,
    reverse_consume,
    reverse_find,
)

fixer = Fixer(
    __name__,
    min_version=(1, 11),
)

MODULE = "django.db.models"
DECORATOR_NAME = "permalink"

# Set when a @models.permalink method is detected, so the django.db import
# visitor knows to add `from django.urls import reverse`.
_state_needs_reverse: MutableMapping[State, bool] = WeakKeyDictionary()


@fixer.register(ast.FunctionDef)
def visit_FunctionDef(
    state: State,
    node: ast.FunctionDef,
    parents: tuple[ast.AST, ...],
) -> Iterable[tuple[Offset, TokenFunc]]:
    if (
        len(node.decorator_list) == 1
        and (decorator := node.decorator_list[0])  # type: ignore [truthy-bool]
        and isinstance(decorator, ast.Attribute)
        and decorator.attr == DECORATOR_NAME
        and isinstance(decorator.value, ast.Name)
        and decorator.value.id == "models"
        and "models" in state.from_imports["django.db"]
        and len(node.body) == 1
        and (ret_node := node.body[0])  # type: ignore [truthy-bool]
        and isinstance(ret_node, ast.Return)
        and isinstance(ret_node.value, ast.Tuple)
        and 2 <= len(ret_node.value.elts) <= 3
    ):
        _state_needs_reverse[state] = True
        yield (
            ast_start_offset(decorator),
            partial(fix_permalink_decorator, node=decorator),
        )
        yield (
            ast_start_offset(ret_node),
            partial(fix_permalink_return, ret_node=ret_node),
        )


@fixer.register(ast.ImportFrom)
def visit_ImportFrom(
    state: State,
    node: ast.ImportFrom,
    parents: tuple[ast.AST, ...],
) -> Iterable[tuple[Offset, TokenFunc]]:
    if (
        node.module == "django.db"
        and is_rewritable_import_from(node)
        and any(alias.name == "models" for alias in node.names)
    ):
        yield (
            ast_start_offset(node),
            partial(fix_models_import, node=node, state=state),
        )


def fix_models_import(
    tokens: list[Token], i: int, *, node: ast.ImportFrom, state: State
) -> None:
    if not _state_needs_reverse.pop(state, False):
        return
    if "reverse" in state.from_imports["django.urls"]:
        return
    _, indent = extract_indent(tokens, i)
    _, j = find_node(tokens, i, node=node)
    insert(tokens, j + 1, new_src=f"{indent}from django.urls import reverse\n")


def fix_permalink_decorator(tokens: list[Token], i: int, *, node: ast.expr) -> None:
    j = find_last_token(tokens, i, node=node)
    k = j + 1
    while tokens[k].name not in ("NEWLINE", "NL"):
        k += 1
    k += 1

    at = reverse_find(tokens, i, name=OP, src="@")
    at = reverse_consume(tokens, at, name=UNIMPORTANT_WS)
    at = reverse_consume(tokens, at, name=INDENT)

    del tokens[at:k]


def fix_permalink_return(
    tokens: list[Token],
    i: int,
    *,
    ret_node: ast.Return,
) -> None:
    assert isinstance(ret_node.value, ast.Tuple)

    j = find(tokens, i, name=NAME, src="return")
    j += 1

    while tokens[j].name not in ("OP", "NAME", "STRING", "NUMBER", "CODE"):
        j += 1

    tuple_start = j

    if tokens[tuple_start].src == "(":
        inner_args, end = parse_call_args(tokens, tuple_start)

        def src_of(start_idx: int, end_idx: int) -> str:
            return "".join(t.src for t in tokens[start_idx:end_idx]).strip()

        parts = [src_of(*inner_args[0])]
        parts.append(f"args={src_of(*inner_args[1])}")
        if len(inner_args) > 2:
            parts.append(f"kwargs={src_of(*inner_args[2])}")

        tokens[tuple_start:end] = [Token("CODE", "reverse(" + ", ".join(parts) + ")")]
    else:
        end = find_last_token(tokens, i, node=ret_node)

        def src_of_range(start_idx: int, end_idx: int) -> str:
            return "".join(t.src for t in tokens[start_idx : end_idx + 1]).strip()

        depth = 0
        comma_positions: list[int] = []
        for k in range(tuple_start, end + 1):
            if tokens[k].src in ("(", "[", "{"):
                depth += 1
            elif tokens[k].src in (")", "]", "}"):
                depth -= 1
            elif tokens[k].src == "," and depth == 0:
                comma_positions.append(k)

        parts = [src_of_range(tuple_start, comma_positions[0] - 1)]
        if len(comma_positions) >= 2:
            parts.append(
                f"args={src_of_range(comma_positions[0] + 1, comma_positions[1] - 1)}"
            )
            parts.append(f"kwargs={src_of_range(comma_positions[1] + 1, end)}")
        else:
            parts.append(f"args={src_of_range(comma_positions[0] + 1, end)}")
        tokens[tuple_start : end + 1] = [
            Token("CODE", "reverse(" + ", ".join(parts) + ")")
        ]

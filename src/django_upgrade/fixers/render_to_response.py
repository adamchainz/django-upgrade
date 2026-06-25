"""
Rewrite render_to_response() to render():
https://docs.djangoproject.com/en/2.0/releases/2.0/#miscellaneous:~:text=django%2Eshortcuts%2Erender%5Fto%5Fresponse
"""

from __future__ import annotations

import ast
from collections.abc import Iterable
from functools import partial
from typing import cast
from weakref import WeakKeyDictionary

from tokenize_rt import Offset, Token

from django_upgrade.ast import (
    ast_start_offset,
    get_module_names,
    is_rewritable_import_from,
)
from django_upgrade.data import Fixer, State, TokenFunc
from django_upgrade.tokens import (
    CODE,
    OP,
    find,
    find_and_replace_name,
    update_import_names,
)

fixer = Fixer(
    __name__,
    min_version=(2, 0),
)

MODULE = "django.shortcuts"
OLD_NAME = "render_to_response"
NEW_NAME = "render"


@fixer.register(ast.ImportFrom)
def visit_ImportFrom(
    state: State,
    node: ast.ImportFrom,
    parents: tuple[ast.AST, ...],
) -> Iterable[tuple[Offset, TokenFunc]]:
    if (
        node.module == MODULE
        and any(alias.name == OLD_NAME and alias.asname is None for alias in node.names)
        and is_rewritable_import_from(node)
        and NEW_NAME not in get_module_names(cast(ast.Module, parents[0]))
        and _all_render_to_response_calls_rewritable(parents[0])
    ):
        yield (
            ast_start_offset(node),
            partial(
                update_import_names,
                node=node,
                name_map={OLD_NAME: NEW_NAME},
            ),
        )


@fixer.register(ast.Call)
def visit_Call(
    state: State,
    node: ast.Call,
    parents: tuple[ast.AST, ...],
) -> Iterable[tuple[Offset, TokenFunc]]:
    if (
        isinstance(node.func, ast.Name)
        and node.func.id == OLD_NAME
        and OLD_NAME in state.from_imports[MODULE]
        and NEW_NAME not in get_module_names(cast(ast.Module, parents[0]))
        and _all_render_to_response_calls_rewritable(parents[0])
    ):
        yield (
            ast_start_offset(node),
            add_request_argument,
        )


_check_cache: WeakKeyDictionary[ast.Module, bool] = WeakKeyDictionary()


def _all_render_to_response_calls_rewritable(module: ast.AST) -> bool:
    assert isinstance(module, ast.Module)
    try:
        return _check_cache[module]
    except KeyError:
        pass

    result = True

    def _walk(
        node: ast.AST,
        innermost: ast.FunctionDef | ast.AsyncFunctionDef | None,
    ) -> None:
        nonlocal result
        if not result:
            return

        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            innermost = node

        if isinstance(node, ast.Name) and node.id == OLD_NAME:
            result = False
            return

        if (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id == OLD_NAME
            and (node.args or node.keywords)
            and innermost is not None
            and innermost.args.args
            and innermost.args.args[0].arg == "request"
            and not any(isinstance(a, ast.Starred) for a in node.args)
            and not any(kw.arg is None for kw in node.keywords)
        ):
            for child in ast.iter_child_nodes(node):
                if child is not node.func:
                    _walk(child, innermost)
            return

        for child in ast.iter_child_nodes(node):
            _walk(child, innermost)

    _walk(module, None)

    _check_cache[module] = result
    return result


def add_request_argument(tokens: list[Token], i: int) -> None:
    j = find(tokens, i, name=OP, src="(")
    tokens.insert(j + 1, Token(name=CODE, src="request, "))
    find_and_replace_name(tokens, i, name=OLD_NAME, new=NEW_NAME)

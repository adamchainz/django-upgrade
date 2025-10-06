"""
Rewrite imports of StringAgg from django.contrib.postgres.aggregates to django.db.models,
wrapping string literal delimiter arguments in Value(), but only if all StringAgg calls
in the file have safe delimiter arguments:
https://docs.djangoproject.com/en/dev/releases/6.0/#models
"""

from __future__ import annotations

import ast
from collections.abc import Iterable
from functools import partial
from weakref import WeakKeyDictionary

from tokenize_rt import Offset, Token

from django_upgrade.ast import ast_start_offset, is_rewritable_import_from
from django_upgrade.data import Fixer, State, TokenFunc
from django_upgrade.tokens import update_import_modules

fixer = Fixer(
    __name__,
    min_version=(6, 0),
)


do_rewrite: WeakKeyDictionary[ast.Module, bool] = WeakKeyDictionary()


@fixer.register(ast.ImportFrom)
def visit_ImportFrom(
    state: State,
    node: ast.ImportFrom,
    parents: tuple[ast.AST, ...],
) -> Iterable[tuple[Offset, TokenFunc]]:
    if (
        (
            node.module == "django.contrib.postgres.aggregates"
            or node.module == "django.contrib.postgres.aggregates.general"
        )
        and is_rewritable_import_from(node)
        and any(
            alias.name == "StringAgg" and alias.asname is None for alias in node.names
        )
    ):
        module = parents[0]
        assert isinstance(module, ast.Module)
        do_rewrite.setdefault(module, True)

        yield (
            ast_start_offset(node),
            partial(rewrite_import_from, node=node, module=module),
        )


@fixer.register(ast.Call)
def visit_Call(
    state: State,
    node: ast.Call,
    parents: tuple[ast.AST, ...],
) -> Iterable[tuple[Offset, TokenFunc]]:
    if (
        isinstance(node.func, ast.Name)
        and node.func.id == "StringAgg"
        and (
            node.func.id in state.from_imports["django.contrib.postgres.aggregates"]
            or node.func.id
            in state.from_imports["django.contrib.postgres.aggregates.general"]
        )
    ):
        module = parents[0]
        assert isinstance(module, ast.Module)

        if do_rewrite.get(module) is not True:
            return

        delimiter = None
        if len(node.args) == 1:
            for kw in node.keywords:
                if kw.arg == "delimiter":
                    delimiter = kw.value
                    break
        elif len(node.args) >= 2:
            delimiter = node.args[1]

        if delimiter is None:
            # Cannot rewrite
            do_rewrite[module] = False
            return

        if isinstance(delimiter, ast.Constant) and isinstance(delimiter.value, str):
            if "Value" in state.from_imports["django.db.models"]:
                wrap = "Value"
            elif "models" in state.from_imports["django.db"]:
                wrap = "models.Value"
            else:
                do_rewrite[module] = False
                return

            yield (
                ast_start_offset(delimiter),
                partial(
                    wrap_delimiter,
                    wrap=wrap,
                ),
            )
        elif (
            isinstance(delimiter, ast.Call)
            and isinstance(delimiter.func, ast.Name)
            and delimiter.func.id == "Value"
            and "Value" in state.from_imports["django.db.models"]
        ):
            # All good.
            pass
        else:
            do_rewrite[module] = False


def rewrite_import_from(
    tokens: list[Token], i: int, *, node: ast.ImportFrom, module: ast.Module
) -> None:
    if do_rewrite.get(module) is not True:
        return

    update_import_modules(
        tokens, i, node=node, module_rewrites={"StringAgg": "django.db.models"}
    )


def wrap_delimiter(tokens: list[Token], i: int, *, wrap: str) -> None:
    tokens[i] = tokens[i]._replace(src=f"{wrap}(" + tokens[i].src + ")")

"""
Rewrite imports of StringAgg from django.contrib.postgres.aggregates to django.db.models,
wrapping string literal delimiter arguments in Value(), but only if all StringAgg calls
in the file have safe delimiter arguments:
https://docs.djangoproject.com/en/dev/releases/6.0/#models
"""

from __future__ import annotations

import ast
from collections.abc import Iterable
from weakref import WeakKeyDictionary

from tokenize_rt import Offset

from django_upgrade.ast import is_rewritable_import_from
from django_upgrade.data import Fixer, State, TokenFunc

fixer = Fixer(
    __name__,
    min_version=(6, 0),
)

module_stringagg_calls_all_fixable: WeakKeyDictionary[ast.Module, bool | None] = (
    WeakKeyDictionary()
)


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
        module_stringagg_calls_all_fixable.setdefault(module, None)
        # schedule a token rewriter that only does stuff if we only found safe calls
        # ...


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
        if len(node.args) < 2:
            module_stringagg_calls_all_fixable[module] = False
            return
        if module_stringagg_calls_all_fixable.get(module) is False:
            return
        delimiter_arg = node.args[1]
        if isinstance(delimiter_arg, ast.Constant) and isinstance(
            delimiter_arg.value, str
        ):
            # safe
            # TODO: rewriting it
            pass
        elif (
            isinstance(delimiter_arg, ast.Call)
            and isinstance(delimiter_arg.func, ast.Name)
            and delimiter_arg.func.id == "Value"
            and "Value" in state.from_imports["django.db.models"]
        ):
            # safe
            pass
        else:
            module_stringagg_calls_all_fixable[module] = False
            return

        module_stringagg_calls_all_fixable[module] |= True

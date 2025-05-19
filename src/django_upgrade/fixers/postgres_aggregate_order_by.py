"""
Rewrite calls to PostgreSQL aggregate functions to use 'order_by' argument instead of 'ordering':
https://docs.djangoproject.com/en/5.2/releases/5.2/#features-deprecated-in-5-2
"""

from __future__ import annotations

import ast
from collections.abc import Iterable
from functools import partial

from tokenize_rt import Offset

from django_upgrade.ast import ast_start_offset
from django_upgrade.data import Fixer, State, TokenFunc
from django_upgrade.tokens import replace

fixer = Fixer(
    __name__,
    min_version=(5, 2),
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
                isinstance(node.func, ast.Name)
                and node.func.id in ("ArrayAgg", "JSONBAgg", "StringAgg")
                and (
                    node.func.id
                    in state.from_imports["django.contrib.postgres.aggregates"]
                    or node.func.id
                    in state.from_imports["django.contrib.postgres.aggregates.general"]
                )
            )
            or (
                isinstance(node.func, ast.Attribute)
                and node.func.attr in ("ArrayAgg", "JSONBAgg", "StringAgg")
                and isinstance(node.func.value, ast.Name)
                and node.func.value.id == "aggregates"
                and "aggregates" in state.from_imports["django.contrib.postgres"]
            )
            or (
                isinstance(node.func, ast.Attribute)
                and node.func.attr in ("ArrayAgg", "JSONBAgg", "StringAgg")
                and isinstance(node.func.value, ast.Name)
                and node.func.value.id == "general"
                and "general"
                in state.from_imports["django.contrib.postgres.aggregates"]
            )
        )
        and (kwarg_names := {k.arg for k in node.keywords})
        and "ordering" in kwarg_names
        and "order_by" not in kwarg_names
    ):
        check_kwarg = [k for k in node.keywords if k.arg == "ordering"][0]
        yield ast_start_offset(check_kwarg), partial(replace, src="order_by")

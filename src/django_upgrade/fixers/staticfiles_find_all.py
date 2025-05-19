"""
Rewrite staticfiles find() calls to use 'find_all' argument instead of 'all':
https://docs.djangoproject.com/en/5.2/releases/5.2/
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
                and node.func.id == "find"
                and "find" in state.from_imports["django.contrib.staticfiles"]
            )
            or (
                isinstance(node.func, ast.Attribute)
                and node.func.attr == "find"
                and isinstance(node.func.value, ast.Name)
                and node.func.value.id == "finders"
                and "finders" in state.from_imports["django.contrib.staticfiles"]
            )
        )
        and (kwarg_names := {k.arg for k in node.keywords})
        and "all" in kwarg_names
        and "find_all" not in kwarg_names
    ):
        all_kwarg = [k for k in node.keywords if k.arg == "all"][0]
        yield ast_start_offset(all_kwarg), partial(replace, src="find_all")

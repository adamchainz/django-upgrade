"""
Rewrite CheckConstraint calls to use 'condition' argument instead of 'check':
https://docs.djangoproject.com/en/5.1/releases/5.1/#id2
"""

from __future__ import annotations

import ast
import sys
from functools import partial
from typing import Iterable

from tokenize_rt import Offset

from django_upgrade.ast import ast_start_offset
from django_upgrade.data import Fixer
from django_upgrade.data import State
from django_upgrade.data import TokenFunc
from django_upgrade.tokens import replace

fixer = Fixer(
    __name__,
    min_version=(5, 1),
)

# Requires lineno/utf8_byte_offset on ast.keyword, added in Python 3.9
if sys.version_info >= (3, 9):

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
                    and node.func.id == "CheckConstraint"
                    and "CheckConstraint" in state.from_imports["django.db.models"]
                )
                or (
                    isinstance(node.func, ast.Attribute)
                    and node.func.attr == "CheckConstraint"
                    and isinstance(node.func.value, ast.Name)
                    and node.func.value.id == "models"
                    and "models" in state.from_imports["django.db"]
                )
            )
            and (kwarg_names := {k.arg for k in node.keywords})
            and "check" in kwarg_names
            and "condition" not in kwarg_names
        ):
            check_kwarg = [k for k in node.keywords if k.arg == "check"][0]
            yield ast_start_offset(check_kwarg), partial(replace, src="condition")

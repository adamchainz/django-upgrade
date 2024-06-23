"""
Rewrite spelling of assertFormsetError and assertQuerysetEqual to include
capitalized “Set”:
https://docs.djangoproject.com/en/4.2/releases/4.2/#miscellaneous
"""

from __future__ import annotations

import ast
from functools import partial
from typing import Iterable

from tokenize_rt import Offset

from django_upgrade.ast import ast_start_offset
from django_upgrade.data import Fixer
from django_upgrade.data import State
from django_upgrade.data import TokenFunc
from django_upgrade.tokens import find_and_replace_name

fixer = Fixer(
    __name__,
    min_version=(4, 2),
    condition=lambda state: state.looks_like_test_file,
)

MODULE = "django.test.testcase"
NAMES = {
    "assertFormsetError": "assertFormSetError",
    "assertQuerysetEqual": "assertQuerySetEqual",
}


@fixer.register(ast.Call)
def visit_Call(
    state: State,
    node: ast.Call,
    parents: tuple[ast.AST, ...],
) -> Iterable[tuple[Offset, TokenFunc]]:
    if (
        isinstance(func := node.func, ast.Attribute)
        and (name := func.attr) in NAMES
        and isinstance(func.value, ast.Name)
        and func.value.id == "self"
    ):
        yield ast_start_offset(func), partial(
            find_and_replace_name, name=name, new=NAMES[name]
        )

"""
Replace spelling of assertFormsetError:
https://docs.djangoproject.com/en/4.2/releases/4.2/#miscellaneous  # noqa: E501
"""
from __future__ import annotations

import ast
from functools import partial
from typing import Iterable

from tokenize_rt import Offset

from django_upgrade.ast import ast_start_offset
from django_upgrade.data import Fixer, State, TokenFunc
from django_upgrade.tokens import find_and_replace_name

fixer = Fixer(
    __name__,
    min_version=(4, 2),
)

MODULE = "django.test.testcase"
NAMES = {
    "assertFormsetError": "assertFormSetError",
    "assertQuerysetEqual": "assertQuerySetEqual",
}


@fixer.register(ast.Attribute)
def visit_Attribute(
    state: State,
    node: ast.Attribute,
    parents: list[ast.AST],
) -> Iterable[tuple[Offset, TokenFunc]]:
    if (
        (name := node.attr) in NAMES
        and isinstance(node.value, ast.Name)
        and node.value.id == "self"
    ):
        yield ast_start_offset(node), partial(
            find_and_replace_name, name=name, new=NAMES[name]
        )

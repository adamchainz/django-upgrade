"""
Rewrite django.core.validator.EmailValidator arguments:
https://docs.djangoproject.com/en/3.2/releases/3.2/#features-deprecated-in-3-2
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
from django_upgrade.tokens import replace_argument_names

fixer = Fixer(
    __name__,
    min_version=(3, 2),
)

MODULE = "django.core.validators"
NAME = "EmailValidator"
KWARGS = {"whitelist": "allowlist"}


@fixer.register(ast.Call)
def visit_Call(
    state: State,
    node: ast.Call,
    parents: list[ast.AST],
) -> Iterable[tuple[Offset, TokenFunc]]:
    if (
        (
            isinstance(node.func, ast.Name)
            and NAME in state.from_imports[MODULE]
            and node.func.id == NAME
        )
        or (
            isinstance(node.func, ast.Attribute)
            and node.func.attr == NAME
            and "validators" in state.from_imports["django.core"]
            and isinstance(node.func.value, ast.Name)
            and node.func.value.id == "validators"
        )
    ) and any(k.arg in KWARGS for k in node.keywords):
        yield ast_start_offset(node), partial(
            replace_argument_names,
            node=node,
            arg_map=KWARGS,
        )

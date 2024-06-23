"""
Replace BaseCommand.requires_system_checks boolean flag by list of checks:
https://docs.djangoproject.com/en/stable/releases/3.2/#deprecated-features-3-2
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
from django_upgrade.tokens import replace

fixer = Fixer(
    __name__,
    min_version=(3, 2),
    condition=lambda state: state.looks_like_command_file,
)


@fixer.register(ast.Assign)
def visit_Assign(
    state: State,
    node: ast.Assign,
    parents: tuple[ast.AST, ...],
) -> Iterable[tuple[Offset, TokenFunc]]:
    if (
        isinstance(parents[-1], ast.ClassDef)
        and len(node.targets) == 1
        and isinstance(node.targets[0], ast.Name)
        and node.targets[0].id == "requires_system_checks"
        and isinstance(node.value, ast.Constant)
        and (node.value.value is True or node.value.value is False)
    ):
        if node.value.value:
            new_src = '"__all__"'
        else:
            new_src = "[]"
        yield ast_start_offset(node.value), partial(replace, src=new_src)

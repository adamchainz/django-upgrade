"""
Replace `list` error message key with `list_invalid` for ModelMultipleChoiceField.
https://docs.djangoproject.com/en/3.1/releases/3.1/#id2
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
    min_version=(3, 1),
)


@fixer.register(ast.Call)
def visit_Call(
    state: State,
    node: ast.Call,
    parents: list[ast.AST],
) -> Iterable[tuple[Offset, TokenFunc]]:
    if (
        (
            (
                isinstance(node.func, ast.Attribute)
                and node.func.attr == "ModelMultipleChoiceField"
                and "forms" in state.from_imports["django"]
                and isinstance(node.func.value, ast.Name)
                and node.func.value.id == "forms"
            )
            or (
                isinstance(node.func, ast.Name)
                and node.func.id == "ModelMultipleChoiceField"
                and node.func.id in state.from_imports["django.forms"]
            )
        )
        and any(
            (error_message_node := kw).arg == "error_messages" for kw in node.keywords
        )
        and isinstance(error_message_node.value, ast.Dict)
        and any(
            (isinstance(key, ast.Constant) and (list_node := key).value == "list")
            for key in error_message_node.value.keys
        )
    ):
        yield ast_start_offset(list_node), partial(replace, src='"invalid_list"')

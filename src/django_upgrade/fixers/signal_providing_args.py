"""
Remove the 'providing_args' argument from Signal():
https://docs.djangoproject.com/en/3.1/releases/3.1/#features-deprecated-in-3-1
"""

from __future__ import annotations

import ast
from functools import partial
from typing import Iterable

from tokenize_rt import UNIMPORTANT_WS
from tokenize_rt import Offset
from tokenize_rt import Token

from django_upgrade.ast import ast_start_offset
from django_upgrade.data import Fixer
from django_upgrade.data import State
from django_upgrade.data import TokenFunc
from django_upgrade.tokens import CODE
from django_upgrade.tokens import COMMENT
from django_upgrade.tokens import INDENT
from django_upgrade.tokens import OP
from django_upgrade.tokens import consume
from django_upgrade.tokens import find
from django_upgrade.tokens import parse_call_args
from django_upgrade.tokens import reverse_consume

fixer = Fixer(
    __name__,
    min_version=(3, 1),
)

MODULE = "django.dispatch"
NAME = "Signal"


@fixer.register(ast.Call)
def visit_Call(
    state: State,
    node: ast.Call,
    parents: tuple[ast.AST, ...],
) -> Iterable[tuple[Offset, TokenFunc]]:
    if (
        isinstance(node.func, ast.Name)
        and NAME in state.from_imports[MODULE]
        and node.func.id == NAME
    ) or (
        isinstance(node.func, ast.Attribute)
        and node.func.attr == NAME
        and isinstance(node.func.value, ast.Name)
        and node.func.value.id == "dispatch"
        and "dispatch" in state.from_imports["django"]
    ):
        if len(node.args) > 0 or any(k.arg == "providing_args" for k in node.keywords):
            yield ast_start_offset(node), partial(
                remove_providing_args,
                node=node,
            )


def remove_providing_args(tokens: list[Token], i: int, *, node: ast.Call) -> None:
    j = find(tokens, i, name=OP, src="(")
    func_args, _ = parse_call_args(tokens, j)

    if len(node.args):
        start_idx, end_idx = func_args[0]
        if len(node.args) == 1:
            del tokens[start_idx:end_idx]
        else:
            # Have to replace with None
            tokens[start_idx:end_idx] = [Token(name=CODE, src="None")]
    else:
        for n, keyword in enumerate(node.keywords):
            if keyword.arg == "providing_args":
                start_idx, end_idx = func_args[n]

                start_idx = reverse_consume(tokens, start_idx, name=UNIMPORTANT_WS)
                start_idx = reverse_consume(tokens, start_idx, name=INDENT)
                if n > 0:
                    start_idx = reverse_consume(tokens, start_idx, name=OP, src=",")

                if n < len(node.keywords) - 1:
                    end_idx = consume(tokens, end_idx, name=UNIMPORTANT_WS)
                    end_idx = consume(tokens, end_idx, name=OP, src=",")
                    end_idx = consume(tokens, end_idx, name=UNIMPORTANT_WS)
                    end_idx = consume(tokens, end_idx, name=COMMENT)
                    end_idx += 1

                del tokens[start_idx:end_idx]

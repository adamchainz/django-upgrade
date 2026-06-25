"""
Remove fail_silently=False from Django mail API calls, since False is the default:
https://docs.djangoproject.com/en/6.1/howto/mailers-migration/#replacing-fail-silently
"""

from __future__ import annotations

import ast
from collections.abc import Iterable
from functools import partial

from tokenize_rt import UNIMPORTANT_WS, Offset, Token

from django_upgrade.ast import ast_start_offset
from django_upgrade.data import Fixer, State, TokenFunc
from django_upgrade.tokens import (
    INDENT,
    OP,
    find,
    find_last_token,
    parse_call_args,
    reverse_consume,
)

fixer = Fixer(
    __name__,
    min_version=(6, 1),
)

MAIL_MODULE = "django.core.mail"
CORE_MODULE = "django.core"
MAIL_NAME = "mail"

MAIL_SEND_FUNCTIONS = frozenset(
    {
        "send_mail",
        "send_mass_mail",
        "mail_admins",
        "mail_managers",
    }
)

EMAIL_MESSAGE_CLASSES = frozenset(
    {
        "EmailMessage",
        "EmailMultiAlternatives",
    }
)


@fixer.register(ast.Call)
def visit_Call(
    state: State,
    node: ast.Call,
    parents: tuple[ast.AST, ...],
) -> Iterable[tuple[Offset, TokenFunc]]:
    if (
        # Mail send functions
        (
            isinstance(node.func, ast.Name)
            and node.func.id in MAIL_SEND_FUNCTIONS
            and node.func.id in state.from_imports[MAIL_MODULE]
        )
        or (
            isinstance(node.func, ast.Attribute)
            and node.func.attr in MAIL_SEND_FUNCTIONS
            and isinstance(node.func.value, ast.Name)
            and node.func.value.id == MAIL_NAME
            and MAIL_NAME in state.from_imports[CORE_MODULE]
        )
        # EmailMessage(...).send()
        or (
            isinstance(node.func, ast.Attribute)
            and node.func.attr == "send"
            and isinstance(node.func.value, ast.Call)
            and (
                (
                    isinstance(node.func.value.func, ast.Name)
                    and node.func.value.func.id in EMAIL_MESSAGE_CLASSES
                )
                or (
                    isinstance(node.func.value.func, ast.Attribute)
                    and node.func.value.func.attr in EMAIL_MESSAGE_CLASSES
                    and isinstance(node.func.value.func.value, ast.Name)
                    and node.func.value.func.value.id == MAIL_NAME
                    and MAIL_NAME in state.from_imports[CORE_MODULE]
                )
            )
        )
    ):
        for kw_idx, kw in enumerate(node.keywords):
            if (
                kw.arg == "fail_silently"
                and isinstance(kw.value, ast.Constant)
                and kw.value.value is False
            ):
                yield (
                    ast_start_offset(node),
                    partial(
                        remove_fail_silently_kwarg,
                        node=node,
                        kwarg_idx=len(node.args) + kw_idx,
                    ),
                )
                break


def remove_fail_silently_kwarg(
    tokens: list[Token],
    i: int,
    *,
    node: ast.Call,
    kwarg_idx: int,
) -> None:
    j = find_last_token(tokens, i, node=node.func)
    open_paren = find(tokens, j, name=OP, src="(")
    func_args, _ = parse_call_args(tokens, open_paren)

    start_idx, end_idx = func_args[kwarg_idx]

    # Walk back over whitespace/indent and the preceding comma
    start_idx = reverse_consume(tokens, start_idx, name=UNIMPORTANT_WS)
    start_idx = reverse_consume(tokens, start_idx, name=INDENT)
    start_idx = reverse_consume(tokens, start_idx, name=OP, src=",")

    del tokens[start_idx:end_idx]

"""
Convert positional arguments to keyword arguments for Django email APIs:
https://docs.djangoproject.com/en/6.0/releases/6.0/#positional-arguments-in-django-core-mail-apis
"""

from __future__ import annotations

import ast
from collections.abc import Iterable
from functools import partial

from tokenize_rt import Offset, Token

from django_upgrade.ast import ast_start_offset
from django_upgrade.data import Fixer, State, TokenFunc
from django_upgrade.tokens import CODE, OP, find, parse_call_args

fixer = Fixer(
    __name__,
    min_version=(6, 0),
)


class APIConfig:
    __slots__ = ("new_posargs", "new_kwargs", "extra_kwargs")

    def __init__(
        self, new_posargs: int, new_kwargs: list[str], extra_kwargs: bool
    ) -> None:
        self.new_posargs = new_posargs
        self.new_kwargs = new_kwargs
        self.extra_kwargs = extra_kwargs


API_CONFIGS = {
    "get_connection": APIConfig(1, ["fail_silently"], True),
    "mail_admins": APIConfig(2, ["fail_silently", "connection", "html_message"], False),
    "mail_managers": APIConfig(
        2, ["fail_silently", "connection", "html_message"], False
    ),
    "send_mail": APIConfig(
        4,
        [
            "fail_silently",
            "auth_user",
            "auth_password",
            "connection",
            "html_message",
        ],
        False,
    ),
    "send_mass_mail": APIConfig(
        1, ["fail_silently", "auth_user", "auth_password", "connection"], False
    ),
    "EmailMessage": APIConfig(
        4,
        [
            "bcc",
            "connection",
            "attachments",
            "headers",
            "cc",
            "reply_to",
        ],
        False,
    ),
    "EmailMultiAlternatives": APIConfig(
        4,
        [
            "bcc",
            "connection",
            "attachments",
            "headers",
            "alternatives",
            "cc",
            "reply_to",
        ],
        False,
    ),
}

MESSAGE_MODULE_NAMES = frozenset({"EmailMessage", "EmailMultiAlternatives"})


@fixer.register(ast.Call)
def visit_Call(
    state: State,
    node: ast.Call,
    parents: tuple[ast.AST, ...],
) -> Iterable[tuple[Offset, TokenFunc]]:
    # Check for direct import or module import and get function config
    if (
        isinstance(node.func, ast.Name)
        and (
            (
                (func_name := node.func.id) in API_CONFIGS
                and func_name in state.from_imports["django.core.mail"]
            )
            or (
                func_name in MESSAGE_MODULE_NAMES
                and func_name in state.from_imports["django.core.mail.message"]
            )
        )
    ) or (
        isinstance(node.func, ast.Attribute)
        and (func_name := node.func.attr) in API_CONFIGS
        and isinstance(node.func.value, ast.Name)
        and (
            (
                node.func.value.id == "mail"
                and "mail" in state.from_imports["django.core"]
            )
            or (
                func_name in MESSAGE_MODULE_NAMES
                and node.func.value.id == "message"
                and "message" in state.from_imports["django.core.mail"]
            )
        )
    ):
        api_config = API_CONFIGS[func_name]
        num_posargs = len(node.args)
        convertible_posargs = num_posargs - api_config.new_posargs

        if convertible_posargs <= 0 or convertible_posargs > len(api_config.new_kwargs):
            return

        convertible_kwargs = api_config.new_kwargs[:convertible_posargs]

        existing_kwargs = {kw.arg for kw in node.keywords}
        if any(kw in existing_kwargs for kw in convertible_kwargs):
            return

        if not api_config.extra_kwargs:
            unknown_kwargs = existing_kwargs - set(api_config.new_kwargs)
            if unknown_kwargs:
                return

        yield (
            ast_start_offset(node),
            partial(
                migrate_api_args,
                api_config=api_config,
                num_posargs=num_posargs,
                convertible_posargs=convertible_posargs,
            ),
        )


def migrate_api_args(
    tokens: list[Token],
    i: int,
    *,
    api_config: APIConfig,
    num_posargs: int,
    convertible_posargs: int,
) -> None:
    """
    Convert excess positional arguments to keyword arguments for email functions.
    Only converts arguments beyond the allowed positional count.
    """
    open_idx = find(tokens, i, name=OP, src="(")
    func_args, _close_idx = parse_call_args(tokens, open_idx)

    for argindex in range(num_posargs - 1, num_posargs - convertible_posargs - 1, -1):
        kwarg = api_config.new_kwargs[argindex - api_config.new_posargs]
        arg_start, arg_end = func_args[argindex]

        actual_arg_start = arg_start
        while actual_arg_start < arg_end and tokens[actual_arg_start].name in (
            "UNIMPORTANT_WS",
            "NL",
        ):
            actual_arg_start += 1
        tokens.insert(actual_arg_start, Token(name=CODE, src=f"{kwarg}="))

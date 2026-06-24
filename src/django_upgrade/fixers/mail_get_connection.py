"""
Replace no-arg get_connection() calls with mailers.default, and remove
inline connection=get_connection() kwargs from mail sending functions:
https://docs.djangoproject.com/en/6.1/howto/mailers-migration/#replacing-get-connection-and-connection-arguments
"""

from __future__ import annotations

import ast
from collections.abc import Iterable
from functools import partial
from weakref import WeakKeyDictionary

from tokenize_rt import UNIMPORTANT_WS, Offset, Token

from django_upgrade.ast import ast_start_offset, is_rewritable_import_from
from django_upgrade.data import Fixer, State, TokenFunc
from django_upgrade.tokens import (
    CODE,
    INDENT,
    OP,
    find,
    find_last_token,
    parse_call_args,
    reverse_consume,
    update_import_names,
)

fixer = Fixer(
    __name__,
    min_version=(6, 1),
)

MAIL_MODULE = "django.core.mail"
CORE_MODULE = "django.core"
MAIL_NAME = "mail"
GET_CONNECTION = "get_connection"
MAILERS = "mailers"

MAIL_SEND_FUNCTIONS = frozenset(
    {
        "send_mail",
        "send_mass_mail",
        "mail_admins",
        "mail_managers",
    }
)


@fixer.register(ast.ImportFrom)
def visit_ImportFrom(
    state: State,
    node: ast.ImportFrom,
    parents: tuple[ast.AST, ...],
) -> Iterable[tuple[Offset, TokenFunc]]:
    if (
        node.module == MAIL_MODULE
        and is_rewritable_import_from(node)
        and any(
            alias.name == GET_CONNECTION and alias.asname is None
            for alias in node.names
        )
    ):
        module = parents[0]
        assert isinstance(module, ast.Module)
        has_args, standalone_no_arg = _direct_get_connection_usage(module)
        if has_args == 0:
            if standalone_no_arg > 0:
                name_map: dict[str, str] = {GET_CONNECTION: MAILERS}
            else:
                name_map = {GET_CONNECTION: ""}
            yield (
                ast_start_offset(node),
                partial(update_import_names, node=node, name_map=name_map),
            )


@fixer.register(ast.Call)
def visit_Call(
    state: State,
    node: ast.Call,
    parents: tuple[ast.AST, ...],
) -> Iterable[tuple[Offset, TokenFunc]]:
    # Replace mail.get_connection() → mail.mailers.default
    if (
        isinstance(node.func, ast.Attribute)
        and node.func.attr == GET_CONNECTION
        and isinstance(node.func.value, ast.Name)
        and node.func.value.id == MAIL_NAME
        and MAIL_NAME in state.from_imports[CORE_MODULE]
        and len(node.args) == 0
        and len(node.keywords) == 0
        and not _is_inline_connection_kwarg(parents)
    ):
        yield (
            ast_start_offset(node),
            partial(
                replace_call,
                node=node,
                new_src=f"{MAIL_NAME}.{MAILERS}.default",
            ),
        )

    # Replace get_connection() → mailers.default (direct import form)
    elif (
        isinstance(node.func, ast.Name)
        and node.func.id == GET_CONNECTION
        and GET_CONNECTION in state.from_imports[MAIL_MODULE]
        and len(node.args) == 0
        and len(node.keywords) == 0
        and not _is_inline_connection_kwarg(parents)
    ):
        module = parents[0]
        assert isinstance(module, ast.Module)
        has_args, _ = _direct_get_connection_usage(module)
        if has_args == 0:
            yield (
                ast_start_offset(node),
                partial(
                    replace_call,
                    node=node,
                    new_src=f"{MAILERS}.default",
                ),
            )

    # Remove connection=get_connection() kwarg from mail send functions
    elif (
        isinstance(node.func, ast.Name)
        and node.func.id in MAIL_SEND_FUNCTIONS
        and node.func.id in state.from_imports[MAIL_MODULE]
    ) or (
        isinstance(node.func, ast.Attribute)
        and node.func.attr in MAIL_SEND_FUNCTIONS
        and isinstance(node.func.value, ast.Name)
        and node.func.value.id == MAIL_NAME
        and MAIL_NAME in state.from_imports[CORE_MODULE]
    ):
        for kw_idx, kw in enumerate(node.keywords):
            if kw.arg == "connection" and _is_no_arg_get_connection(kw.value, state):
                yield (
                    ast_start_offset(node),
                    partial(
                        remove_connection_kwarg,
                        node=node,
                        kwarg_idx=len(node.args) + kw_idx,
                    ),
                )
                break


def _is_inline_connection_kwarg(parents: tuple[ast.AST, ...]) -> bool:
    """Return True if the node is a connection= kwarg in a mail send function call."""
    return (
        len(parents) >= 2
        and isinstance(parents[-1], ast.keyword)
        and parents[-1].arg == "connection"
        and isinstance(parents[-2], ast.Call)
        and (
            (
                isinstance(parents[-2].func, ast.Name)
                and parents[-2].func.id in MAIL_SEND_FUNCTIONS
            )
            or (
                isinstance(parents[-2].func, ast.Attribute)
                and parents[-2].func.attr in MAIL_SEND_FUNCTIONS
            )
        )
    )


_direct_get_connection_usage_cache: WeakKeyDictionary[ast.Module, tuple[int, int]] = (
    WeakKeyDictionary()
)


def _direct_get_connection_usage(
    module: ast.Module,
) -> tuple[int, int]:
    """
    Walk the module counting usages of get_connection() via direct import
    (Name('get_connection') calls).

    Returns (has_args_count, standalone_no_arg_count).
    'standalone' means not used as an inline connection= kwarg in a mail function.
    """
    try:
        return _direct_get_connection_usage_cache[module]
    except KeyError:
        pass

    has_args = 0
    standalone_no_arg = 0

    stack: list[tuple[ast.AST, tuple[ast.AST, ...]]] = [(module, ())]
    while stack:
        node, parents = stack.pop()
        if (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id == GET_CONNECTION
        ):
            if len(node.args) > 0 or len(node.keywords) > 0:
                has_args += 1
            elif not _is_inline_connection_kwarg(parents):
                standalone_no_arg += 1
        subparents = parents + (node,)
        for child in ast.iter_child_nodes(node):
            stack.append((child, subparents))

    result = has_args, standalone_no_arg
    _direct_get_connection_usage_cache[module] = result
    return result


def _is_no_arg_get_connection(node: ast.expr, state: State) -> bool:
    """Return True if node is a no-arg get_connection() call (either import form)."""
    return (
        isinstance(node, ast.Call)
        and len(node.args) == 0
        and len(node.keywords) == 0
        and (
            (
                isinstance(node.func, ast.Name)
                and node.func.id == GET_CONNECTION
                and GET_CONNECTION in state.from_imports[MAIL_MODULE]
            )
            or (
                isinstance(node.func, ast.Attribute)
                and node.func.attr == GET_CONNECTION
                and isinstance(node.func.value, ast.Name)
                and node.func.value.id == MAIL_NAME
                and MAIL_NAME in state.from_imports[CORE_MODULE]
            )
        )
    )


def replace_call(tokens: list[Token], i: int, *, node: ast.Call, new_src: str) -> None:
    j = find_last_token(tokens, i, node=node)
    tokens[i : j + 1] = [Token(name=CODE, src=new_src)]


def remove_connection_kwarg(
    tokens: list[Token], i: int, *, node: ast.Call, kwarg_idx: int
) -> None:
    open_paren = find(tokens, i, name=OP, src="(")
    func_args, _ = parse_call_args(tokens, open_paren)

    start_idx, end_idx = func_args[kwarg_idx]

    # Walk back over whitespace/indent and the preceding comma
    start_idx = reverse_consume(tokens, start_idx, name=UNIMPORTANT_WS)
    start_idx = reverse_consume(tokens, start_idx, name=INDENT)
    start_idx = reverse_consume(tokens, start_idx, name=OP, src=",")

    del tokens[start_idx:end_idx]

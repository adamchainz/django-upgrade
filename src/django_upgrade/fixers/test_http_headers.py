"""
Transforms HTTP headers from WSGI kwarg format to new 'headers' dictionary, for
test Client and RequestFactory:
https://docs.djangoproject.com/en/4.2/releases/4.2/#tests
"""
from __future__ import annotations

import ast
from functools import partial
from typing import Iterable

from tokenize_rt import Offset
from tokenize_rt import Token

from django_upgrade.ast import ast_start_offset
from django_upgrade.compat import str_removeprefix
from django_upgrade.data import Fixer
from django_upgrade.data import State
from django_upgrade.data import TokenFunc
from django_upgrade.fixers.assert_form_error import looks_like_client_call
from django_upgrade.tokens import find
from django_upgrade.tokens import NAME
from django_upgrade.tokens import OP
from django_upgrade.tokens import parse_call_args

fixer = Fixer(
    __name__,
    min_version=(4, 2),
)

HEADERS_KWARG = "headers"
HTTP_PREFIX = "HTTP_"


@fixer.register(ast.Call)
def visit_Call(
    state: State,
    node: ast.Call,
    parents: list[ast.AST],
) -> Iterable[tuple[Offset, TokenFunc]]:
    if (
        state.looks_like_test_file
        and (
            (
                isinstance(node.func, ast.Name)
                and node.func.id in ("Client", "RequestFactory")
                and node.func.id in state.from_imports["django.test"]
            )
            or (looks_like_client_call(node, "client") and node.args)
        )
        and any(
            kw.arg is not None and kw.arg.startswith(HTTP_PREFIX)
            for kw in node.keywords
        )
    ):
        yield ast_start_offset(node), partial(
            merge_http_headers_kwargs,
            node=node,
        )


def merge_http_headers_kwargs(tokens: list[Token], i: int, *, node: ast.Call) -> None:
    http_kwargs_names = []
    contains_headers_kwarg = False

    for kw in node.keywords:
        if kw.arg and kw.arg.startswith(HTTP_PREFIX):
            http_kwargs_names.append(kw.arg)
        elif kw.arg == HEADERS_KWARG:
            contains_headers_kwarg = True

    new_headers_kwarg_values = {}
    first_start_idx = -1
    for http_kwarg_name in http_kwargs_names:
        erased_tokens, start_idx = erase_keyword_argument(
            tokens, i, kwarg_name=http_kwarg_name
        )
        new_headers_kwarg_values[transform_header_arg(http_kwarg_name)] = erased_tokens
        if first_start_idx == -1:
            first_start_idx = start_idx

    if new_headers_kwarg_values:
        if contains_headers_kwarg:
            insert_into_existing_headers_kwarg(
                tokens, i, kwarg_dict=new_headers_kwarg_values
            )
        else:
            insert_headers_kwarg(
                tokens,
                i,
                kwarg_dict=new_headers_kwarg_values,
                insert_position=first_start_idx,
            )


def transform_header_arg(header: str) -> str:
    return str_removeprefix(header, HTTP_PREFIX).replace("_", "-").lower()


def erase_keyword_argument(
    tokens: list[Token], i: int, *, kwarg_name: str
) -> tuple[list[Token], int]:
    """
    Erases a keyword argument based on its name, and returns the tokens that
    defined the value of the keyword argument, and its starting position.
    The starting position will be used to start inserting the new argument in
    the right place.
    """
    open_idx = find(tokens, i, name=OP, src="(")
    func_args, close_idx = parse_call_args(tokens, open_idx)
    for arg_start_idx, arg_end_idx in func_args:
        kwarg_name_start_idx = find(tokens, arg_start_idx, name=NAME, src=kwarg_name)
        if kwarg_name_start_idx > arg_end_idx:
            continue

        value_start_idx = find(tokens, kwarg_name_start_idx, name=OP, src="=")
        erased_tokens = tokens[value_start_idx + 1 : arg_end_idx]

        ends_with_comma = (
            tokens[arg_end_idx].name == OP and tokens[arg_end_idx].src == ","
        )
        if ends_with_comma:
            arg_end_idx += 1
        ends_with_whitespace = (
            tokens[arg_end_idx].name == "UNIMPORTANT_WS"
            and tokens[arg_end_idx].src == " "
        )
        if ends_with_whitespace:
            arg_end_idx += 1

        del tokens[kwarg_name_start_idx:arg_end_idx]
        return erased_tokens, kwarg_name_start_idx
    return [], -1


def insert_into_existing_headers_kwarg(
    tokens: list[Token], i: int, *, kwarg_dict: dict[str, list[Token]]
) -> None:
    open_idx = find(tokens, i, name=OP, src="(")

    headers_arg_start_idx = find(tokens, open_idx, name=NAME, src=HEADERS_KWARG)
    headers_closing_idx = find(tokens, headers_arg_start_idx, name=OP, src="}")

    new_tokens = []
    for key, value in kwarg_dict.items():
        new_tokens += [
            Token(name="OP", src=","),
            Token(name="UNIMPORTANT_WS", src=" "),
        ]
        new_tokens += [
            Token(name="STRING", src=f'"{key}"'),
            Token(name="OP", src=":"),
            Token(name="UNIMPORTANT_WS", src=" "),
        ]
        new_tokens += value
    tokens[headers_closing_idx:headers_closing_idx] = new_tokens


def insert_headers_kwarg(
    tokens: list[Token],
    i: int,
    *,
    kwarg_dict: dict[str, list[Token]],
    insert_position: int,
) -> None:
    open_idx = find(tokens, i, name=OP, src="(")
    func_args, close_idx = parse_call_args(tokens, open_idx)

    new_tokens = [
        Token(name=NAME, src=HEADERS_KWARG),
        Token(name="OP", src="="),
        Token(name="OP", src="{"),
    ]

    for i, (key, value) in enumerate(kwarg_dict.items(), 1):
        new_tokens += [
            Token(name="STRING", src=f'"{key}"'),
            Token(name="OP", src=":"),
            Token(name="UNIMPORTANT_WS", src=" "),
        ]
        new_tokens += value
        if i < len(kwarg_dict):
            new_tokens += [
                Token(name="OP", src=","),
                Token(name="UNIMPORTANT_WS", src=" "),
            ]

    new_tokens += [
        Token(name="OP", src="}"),
    ]

    # If it's not the last argument.
    if len(func_args) != 0 and func_args[-1][1] > insert_position:
        new_tokens += [
            Token(name="OP", src=","),
            Token(name="UNIMPORTANT_WS", src=" "),
        ]

    tokens[insert_position:insert_position] = new_tokens

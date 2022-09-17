"""
Update use of request.META to fetch headers to use request.headers
https://docs.djangoproject.com/en/2.2/releases/2.2/#requests-and-responses
"""
from __future__ import annotations

import ast
import sys
from functools import partial
from typing import Iterable

from tokenize_rt import Offset, Token

from django_upgrade.ast import ast_start_offset
from django_upgrade.data import Fixer, State, TokenFunc
from django_upgrade.tokens import NAME, STRING, find, replace

fixer = Fixer(
    __name__,
    min_version=(2, 2),
)


def get_http_header_name(meta_name: str) -> str | None:
    """Extract HTTP header name, unless it isn't an HTTP header."""
    http_prefix = "HTTP_"
    if meta_name.startswith(http_prefix):
        return meta_name[len(http_prefix) :]
    if meta_name in {"CONTENT_LENGTH", "CONTENT_TYPE"}:
        return meta_name
    return None


@fixer.register(ast.Subscript)
def visit_Subscript(
    state: State,
    node: ast.Subscript,
    parents: list[ast.AST],
) -> Iterable[tuple[Offset, TokenFunc]]:
    if (
        not isinstance(parents[-1], ast.Assign)
        and is_request_or_self_request_meta(node.value)
        and (meta_name := extract_constant(node.slice)) is not None
        and (raw_header_name := get_http_header_name(meta_name)) is not None
    ):
        yield ast_start_offset(node), partial(
            rewrite_header_access, raw_header_name=raw_header_name
        )


@fixer.register(ast.Call)
def visit_Call(
    state: State,
    node: ast.Call,
    parents: list[ast.AST],
) -> Iterable[tuple[Offset, TokenFunc]]:
    if (
        isinstance(node.func, ast.Attribute)
        and node.func.attr == "get"
        and is_request_or_self_request_meta(node.func.value)
        and len(node.args) >= 1
        and isinstance(node.args[0], ast.Constant)
        and isinstance(meta_name := node.args[0].value, str)
        and (raw_header_name := get_http_header_name(meta_name)) is not None
    ):
        yield ast_start_offset(node), partial(
            rewrite_header_access, raw_header_name=raw_header_name
        )


def is_request_or_self_request_meta(node: ast.AST) -> bool:
    return (
        isinstance(node, ast.Attribute)
        and node.attr == "META"
        and (
            (isinstance(node.value, ast.Name) and node.value.id == "request")
            or (
                isinstance(node.value, ast.Attribute)
                and isinstance(node.value.value, ast.Name)
                and node.value.value.id == "self"
                and node.value.attr == "request"
            )
        )
    )


if sys.version_info >= (3, 9):

    def extract_constant(node: ast.AST) -> str | None:
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            return node.value
        return None

else:

    def extract_constant(node: ast.AST) -> str | None:
        if (
            isinstance(node, ast.Index)
            and isinstance(node.value, ast.Constant)
            and isinstance(node.value.value, str)
        ):
            return node.value.value
        return None


def rewrite_header_access(tokens: list[Token], i: int, *, raw_header_name: str) -> None:
    meta_idx = find(tokens, i, name=NAME, src="META")
    replace(tokens, meta_idx, src="headers")

    str_idx = find(tokens, meta_idx, name=STRING)
    header_name = "-".join(x.title() for x in raw_header_name.split("_"))
    replace(tokens, str_idx, src=repr(header_name))

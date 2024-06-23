"""
Update use of request.META to fetch headers to use request.headers
https://docs.djangoproject.com/en/2.2/releases/2.2/#requests-and-responses
"""

from __future__ import annotations

import ast
import sys
from functools import partial
from typing import Iterable

from tokenize_rt import Offset
from tokenize_rt import Token

from django_upgrade.ast import ast_start_offset
from django_upgrade.data import Fixer
from django_upgrade.data import State
from django_upgrade.data import TokenFunc
from django_upgrade.tokens import NAME
from django_upgrade.tokens import STRING
from django_upgrade.tokens import find
from django_upgrade.tokens import replace
from django_upgrade.tokens import str_repr_matching

fixer = Fixer(
    __name__,
    min_version=(2, 2),
)


@fixer.register(ast.Subscript)
def visit_Subscript(
    state: State,
    node: ast.Subscript,
    parents: tuple[ast.AST, ...],
) -> Iterable[tuple[Offset, TokenFunc]]:
    if (
        is_request_or_self_request_meta(node.value)
        and not isinstance(parents[-1], ast.Delete)
        and not (isinstance(parents[-1], ast.Assign) and node in parents[-1].targets)
        and (meta_name := extract_constant(node.slice)) is not None
        and (header_name := get_header_name(meta_name)) is not None
    ):
        yield ast_start_offset(node), partial(
            rewrite_header_access, header_name=header_name
        )


@fixer.register(ast.Call)
def visit_Call(
    state: State,
    node: ast.Call,
    parents: tuple[ast.AST, ...],
) -> Iterable[tuple[Offset, TokenFunc]]:
    if (
        isinstance(node.func, ast.Attribute)
        and node.func.attr == "get"
        and is_request_or_self_request_meta(node.func.value)
        and len(node.args) >= 1
        and isinstance(node.args[0], ast.Constant)
        and isinstance(meta_name := node.args[0].value, str)
        and (header_name := get_header_name(meta_name)) is not None
    ):
        yield ast_start_offset(node), partial(
            rewrite_header_access, header_name=header_name
        )


@fixer.register(ast.Compare)
def visit_Compare(
    state: State,
    node: ast.Compare,
    parents: tuple[ast.AST, ...],
) -> Iterable[tuple[Offset, TokenFunc]]:
    if (
        len(node.ops) == 1
        and isinstance(node.ops[0], (ast.In, ast.NotIn))
        and len(node.comparators) == 1
        and is_request_or_self_request_meta(node.comparators[0])
        and isinstance(node.left, ast.Constant)
        and (header_name := get_header_name(node.left.value)) is not None
    ):
        yield ast_start_offset(node), partial(
            rewrite_in_statement, header_name=header_name
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


def get_header_name(meta_name: str) -> str | None:
    """Extract HTTP header name, unless it isn't an HTTP header."""
    http_prefix = "HTTP_"
    if meta_name.startswith(http_prefix):
        name = meta_name[len(http_prefix) :]
    elif meta_name in {"CONTENT_LENGTH", "CONTENT_TYPE"}:
        name = meta_name
    else:
        return None
    return "-".join(x for x in name.lower().split("_"))


def rewrite_header_access(tokens: list[Token], i: int, *, header_name: str) -> None:
    meta_idx = find(tokens, i, name=NAME, src="META")
    replace(tokens, meta_idx, src="headers")
    str_idx = find(tokens, meta_idx, name=STRING)
    header_src = str_repr_matching(header_name, match_quotes=tokens[str_idx].src)
    replace(tokens, str_idx, src=header_src)


def rewrite_in_statement(tokens: list[Token], i: int, *, header_name: str) -> None:
    header_src = str_repr_matching(header_name, match_quotes=tokens[i].src)
    replace(tokens, i, src=header_src)
    meta_idx = find(tokens, i, name=NAME, src="META")
    replace(tokens, meta_idx, src="headers")

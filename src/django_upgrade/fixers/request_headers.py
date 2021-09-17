"""
Update use of request.META to fetch headers to use request.headers
https://docs.djangoproject.com/en/2.2/releases/2.2/#requests-and-responses
"""
import ast
import sys
from functools import partial
from typing import Iterable, List, Optional, Tuple

from tokenize_rt import Offset, Token

from django_upgrade.ast import ast_start_offset
from django_upgrade.data import Fixer, State, TokenFunc
from django_upgrade.tokens import NAME, STRING, find, replace

fixer = Fixer(
    __name__,
    min_version=(2, 2),
)


@fixer.register(ast.Subscript)
def visit_Subscript(
    state: State,
    node: ast.Subscript,
    parent: ast.AST,
) -> Iterable[Tuple[Offset, TokenFunc]]:
    if (
        is_request_or_self_request_meta(node.value)
        and (meta_name := extract_constant(node.slice)) is not None
        and meta_name.startswith("HTTP_")
    ):
        yield ast_start_offset(node), partial(
            rewrite_header_access, meta_name=meta_name
        )


@fixer.register(ast.Call)
def visit_Call(
    state: State,
    node: ast.Call,
    parent: ast.AST,
) -> Iterable[Tuple[Offset, TokenFunc]]:
    if (
        isinstance(node.func, ast.Attribute)
        and node.func.attr == "get"
        and is_request_or_self_request_meta(node.func.value)
        and len(node.args) >= 1
        and isinstance(node.args[0], ast.Constant)
        and isinstance(meta_name := node.args[0].value, str)
        and meta_name.startswith("HTTP_")
    ):
        yield ast_start_offset(node), partial(
            rewrite_header_access, meta_name=meta_name
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

    def extract_constant(node: ast.AST) -> Optional[str]:
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            return node.value
        return None


else:

    def extract_constant(node: ast.AST) -> Optional[str]:
        if (
            isinstance(node, ast.Index)
            and isinstance(node.value, ast.Constant)
            and isinstance(node.value.value, str)
        ):
            return node.value.value
        return None


def rewrite_header_access(tokens: List[Token], i: int, *, meta_name: str) -> None:
    meta_idx = find(tokens, i, name=NAME, src="META")
    replace(tokens, meta_idx, src="headers")

    str_idx = find(tokens, meta_idx, name=STRING)
    raw_header_name = meta_name[len("HTTP_") :]
    header_name = "-".join(x.title() for x in raw_header_name.split("_"))
    replace(tokens, str_idx, src=repr(header_name))

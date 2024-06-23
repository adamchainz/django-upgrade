"""
Transforms HTTP headers from WSGI kwarg format to new 'headers' dictionary, for
test Client and RequestFactory:
https://docs.djangoproject.com/en/4.2/releases/4.2/#tests
"""

from __future__ import annotations

import ast
import sys
from bisect import bisect
from functools import partial
from typing import Iterable
from typing import cast

from tokenize_rt import UNIMPORTANT_WS
from tokenize_rt import Offset
from tokenize_rt import Token

from django_upgrade.ast import ast_start_offset
from django_upgrade.ast import looks_like_test_client_call
from django_upgrade.compat import str_removeprefix
from django_upgrade.data import Fixer
from django_upgrade.data import State
from django_upgrade.data import TokenFunc
from django_upgrade.tokens import COMMENT
from django_upgrade.tokens import OP
from django_upgrade.tokens import PHYSICAL_NEWLINE
from django_upgrade.tokens import consume
from django_upgrade.tokens import find
from django_upgrade.tokens import find_first_token
from django_upgrade.tokens import find_last_token
from django_upgrade.tokens import insert

fixer = Fixer(
    __name__,
    min_version=(4, 2),
    condition=lambda state: state.looks_like_test_file,
)

HEADERS_KWARG = "headers"
HTTP_PREFIX = "HTTP_"

# Requires lineno/utf8_byte_offset on ast.keyword, added in Python 3.9
if sys.version_info >= (3, 9):

    @fixer.register(ast.Call)
    def visit_Call(
        state: State,
        node: ast.Call,
        parents: tuple[ast.AST, ...],
    ) -> Iterable[tuple[Offset, TokenFunc]]:
        if (
            isinstance(node.func, ast.Name)
            and node.func.id in ("Client", "RequestFactory")
            and node.func.id in state.from_imports["django.test"]
        ) or looks_like_test_client_call(node, "client"):
            has_http_kwarg = False
            headers_keyword = None
            for keyword in node.keywords:
                if keyword.arg is None:  # ** unpacking
                    return
                elif keyword.arg == "headers":
                    if not isinstance(keyword.value, ast.Dict):
                        return
                    headers_keyword = keyword
                elif keyword.arg.startswith(HTTP_PREFIX):
                    has_http_kwarg = True

            if has_http_kwarg:
                yield ast_start_offset(node), partial(
                    combine_http_headers_kwargs,
                    node=node,
                    headers_keyword=headers_keyword,
                )


class Insert:
    def __init__(self, src: str) -> None:
        self.src = src


class Delete:
    def __init__(self, end: int) -> None:
        self.end = end


def combine_http_headers_kwargs(
    tokens: list[Token], i: int, *, node: ast.Call, headers_keyword: ast.keyword | None
) -> None:
    if headers_keyword is not None:
        existing_headers_idx = find_last_token(tokens, i, node=headers_keyword)
        existing_headers_needs_comma = (
            len(cast(ast.Dict, headers_keyword.value).keys) > 0
        )
    else:
        existing_headers_idx = 0
        existing_headers_needs_comma = False

    j = i
    src_fragments = []
    operations: list[tuple[int, Insert | Delete]] = []
    kwargs_after_first_http_kwarg = False

    for keyword in node.keywords:
        assert keyword.arg is not None
        if keyword.arg.startswith(HTTP_PREFIX):
            if operations:
                src_fragments.append(", ")

            header_name = transform_header_arg(keyword.arg)
            src_fragments.append(f'"{header_name}": ')

            kw_start = find_first_token(tokens, j, node=keyword)
            j = find(tokens, kw_start, name=OP, src="=") + 1
            k = find_last_token(tokens, j, node=keyword)
            src_fragments.extend([t.src for t in tokens[j : k + 1]])

            # Remove indentation
            if (
                (headers_keyword is not None or operations)
                and tokens[kw_start - 1].name == UNIMPORTANT_WS
                and tokens[kw_start - 2].name == PHYSICAL_NEWLINE
            ):
                kw_start -= 1
            kw_end = consume(tokens, k, name=OP, src=",")
            if (
                tokens[kw_end + 1].name == UNIMPORTANT_WS
                and tokens[kw_end + 2].name != COMMENT
            ):
                kw_end += 1
            if headers_keyword is not None or operations:
                kw_end = consume(tokens, kw_end, name=PHYSICAL_NEWLINE)
            operations.append((kw_start, Delete(kw_end)))
        elif operations:
            kwargs_after_first_http_kwarg = True

    if headers_keyword is not None:
        if existing_headers_needs_comma:
            src_fragments.insert(0, ", ")
        insert_op = (
            existing_headers_idx,
            Insert("".join(src_fragments)),
        )
        operations.insert(bisect(operations, insert_op), insert_op)
    else:
        src_fragments.insert(0, "headers={")
        src_fragments.append("}")
        if kwargs_after_first_http_kwarg:
            src_fragments.append(", ")
        operations.insert(
            0,
            (
                operations[0][0],
                Insert("".join(src_fragments)),
            ),
        )

    for pos, operation in reversed(operations):
        if isinstance(operation, Insert):
            insert(tokens, pos, new_src=operation.src)
        else:
            assert isinstance(operation, Delete)
            del tokens[pos : operation.end + 1]


def transform_header_arg(header: str) -> str:
    return str_removeprefix(header, HTTP_PREFIX).replace("_", "-").lower()

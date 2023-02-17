from __future__ import annotations

import ast
import warnings
from typing import Literal

from tokenize_rt import Offset


def ast_parse(contents_text: str) -> ast.Module:
    # intentionally ignore warnings, we can't do anything about them
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        return ast.parse(contents_text.encode())


def ast_start_offset(node: ast.expr | ast.keyword | ast.stmt) -> Offset:
    return Offset(node.lineno, node.col_offset)


def is_rewritable_import_from(node: ast.ImportFrom) -> bool:
    # Not relative import or import *
    return node.level == 0 and not (len(node.names) == 1 and node.names[0].name == "*")


TEST_CLIENT_REQUEST_METHODS = frozenset(
    (
        "request",
        "get",
        "post",
        "head",
        "options",
        "put",
        "patch",
        "delete",
        "trace",
    )
)


def looks_like_test_client_call(
    node: ast.AST, client_name: Literal["async_client", "client"]
) -> bool:
    return (
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr in TEST_CLIENT_REQUEST_METHODS
        and isinstance(node.func.value, ast.Attribute)
        and node.func.value.attr == client_name
        and isinstance(node.func.value.value, ast.Name)
        and node.func.value.value.id == "self"
    )

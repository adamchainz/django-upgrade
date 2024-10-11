from __future__ import annotations

import ast
import warnings
from typing import TYPE_CHECKING
from typing import Literal
from typing import cast

from tokenize_rt import Offset

if TYPE_CHECKING:
    from django_upgrade.data import State


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


def is_passing_comparison(
    test: ast.Compare, state: State
) -> Literal["pass", "fail", None]:
    """
    Return whether the given ast.Compare node compares a version tuple with
    django.VERSION and would pass or fail for the current target version, or
    None if no match or cannot determine.
    """
    if not (
        isinstance(left := test.left, ast.Attribute)
        and isinstance(left.value, ast.Name)
        and left.value.id == "django"
        and left.attr == "VERSION"
        and len(test.ops) == 1
        and isinstance(test.ops[0], (ast.Gt, ast.GtE, ast.Lt, ast.LtE))
        and len(test.comparators) == 1
        and isinstance((comparator := test.comparators[0]), ast.Tuple)
        and len(comparator.elts) == 2
        and all(isinstance(e, ast.Constant) for e in comparator.elts)
        and all(isinstance(cast(ast.Constant, e).value, int) for e in comparator.elts)
    ):
        return None

    min_version = tuple(cast(ast.Constant, e).value for e in comparator.elts)
    if isinstance(test.ops[0], ast.Gt):
        if state.settings.target_version > min_version:
            return "pass"
    elif isinstance(test.ops[0], ast.GtE):
        if state.settings.target_version >= min_version:
            return "pass"
    elif isinstance(test.ops[0], ast.Lt):
        if state.settings.target_version >= min_version:
            return "fail"
    else:  # ast.LtE
        if state.settings.target_version > min_version:
            return "fail"
    return None

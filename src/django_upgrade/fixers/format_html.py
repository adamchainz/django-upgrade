"""
Rewrite some format_html() calls passing formatted strings without other
arguments or keyword arguments to use the format_html formatting.

https://docs.djangoproject.com/en/5.0/releases/5.0/#features-deprecated-in-5-0
"""

from __future__ import annotations

import ast
from functools import partial
from typing import Iterable

from tokenize_rt import Offset
from tokenize_rt import Token

from django_upgrade.ast import ast_start_offset
from django_upgrade.data import Fixer
from django_upgrade.data import State
from django_upgrade.data import TokenFunc
from django_upgrade.tokens import OP
from django_upgrade.tokens import alone_on_line
from django_upgrade.tokens import find
from django_upgrade.tokens import find_last_token
from django_upgrade.tokens import insert

fixer = Fixer(
    __name__,
    min_version=(5, 0),
)


@fixer.register(ast.Call)
def visit_Call(
    state: State,
    node: ast.Call,
    parents: tuple[ast.AST, ...],
) -> Iterable[tuple[Offset, TokenFunc]]:
    if (
        "format_html" in state.from_imports["django.utils.html"]
        and isinstance(node.func, ast.Name)
        and node.func.id == "format_html"
        # Template only
        and len(node.args) == 1
        and len(node.keywords) == 0
        # str.format()
        and isinstance((str_format := node.args[0]), ast.Call)
        and isinstance(str_format.func, ast.Attribute)
        and isinstance(str_format.func.value, ast.Constant)
        and isinstance(str_format.func.value.value, str)
        and str_format.func.attr == "format"
    ):
        yield ast_start_offset(node), partial(rewrite_str_format, node=str_format)


def rewrite_str_format(
    tokens: list[Token],
    i: int,
    *,
    node: ast.Call,
) -> None:
    open_start = find(tokens, i, name=OP, src=".")
    open_end = find(tokens, open_start, name=OP, src="(")

    # closing paren
    cp_start = cp_end = find_last_token(tokens, open_end, node=node)
    if alone_on_line(tokens, cp_start, cp_end):
        cp_start -= 1
        cp_end += 1

    del tokens[cp_start : cp_end + 1]
    del tokens[open_start : open_end + 1]
    insert(tokens, open_start, new_src=", ")

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
from django_upgrade.tokens import replace

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
    ):
        arg = node.args[0]

        # String constant -> mark_safe()
        if (
            isinstance(arg, ast.Constant)
            and isinstance(arg.value, str)
            and "mark_safe" in state.from_imports["django.utils.safestring"]
        ):
            yield ast_start_offset(node), partial(replace, src="mark_safe")

        # str.format() -> push args and kwargs out to format_html
        elif (
            isinstance(arg, ast.Call)
            and isinstance(arg.func, ast.Attribute)
            and arg.func.attr == "format"
            and isinstance(arg.func.value, ast.Constant)
            and isinstance(arg.func.value.value, str)
        ):
            yield ast_start_offset(arg), partial(rewrite_str_format, node=arg)


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

"""
Rewrite django.utils.timezone.FixedOffset to datetime.timezone.
https://docs.djangoproject.com/en/2.2/releases/2.2/#features-deprecated-in-2-2
"""
import ast
from functools import partial
from typing import Iterable, List, Tuple

from tokenize_rt import Offset, Token

from django_upgrade.ast import ast_start_offset
from django_upgrade.data import Fixer, State, TokenFunc
from django_upgrade.tokens import (
    OP,
    extract_indent,
    find,
    insert,
    parse_call_args,
    replace,
    update_import_names,
)

fixer = Fixer(
    __name__,
    min_version=(2, 2),
)

MODULE = "django.utils.timezone"
OLD_NAME = "FixedOffset"


@fixer.register(ast.ImportFrom)
def visit_ImportFrom(
    state: State,
    node: ast.ImportFrom,
    parent: ast.AST,
) -> Iterable[Tuple[Offset, TokenFunc]]:
    if (
        node.level == 0
        and node.module == MODULE
        and any(alias.name == OLD_NAME for alias in node.names)
    ):
        yield ast_start_offset(node), partial(fix_import_from, node=node)


def fix_import_from(tokens: List[Token], i: int, *, node: ast.ImportFrom) -> None:
    j, indent = extract_indent(tokens, i)
    update_import_names(tokens, i, node=node, name_map={OLD_NAME: ""})
    insert(tokens, j, new_src=f"{indent}from datetime import timedelta, timezone\n")


@fixer.register(ast.Call)
def visit_Call(
    state: State,
    node: ast.Call,
    parent: ast.AST,
) -> Iterable[Tuple[Offset, TokenFunc]]:
    if (
        OLD_NAME in state.from_imports[MODULE]
        and isinstance(node.func, ast.Name)
        and node.func.id == OLD_NAME
    ):
        yield ast_start_offset(node), partial(fix_offset_arg, node=node)


def fix_offset_arg(tokens: List[Token], i: int, *, node: ast.Call) -> None:
    j = find(tokens, i, name=OP, src="(")
    func_args, _ = parse_call_args(tokens, j)

    rewrote_offset_arg = False
    if len(node.args) >= 1:
        if not isinstance(node.args[0], ast.Starred):
            start_idx, end_idx = func_args[0]
            insert(tokens, end_idx, new_src=")")
            insert(tokens, start_idx, new_src="timedelta(minutes=")
            rewrote_offset_arg = True
    else:
        for n, keyword in enumerate(node.keywords):
            if keyword.arg == "offset":
                start_idx, end_idx = func_args[n]
                insert(tokens, end_idx, new_src=")")
                equal_idx = find(tokens, start_idx, name=OP, src="=")
                insert(tokens, equal_idx + 1, new_src="timedelta(minutes=")
                rewrote_offset_arg = True

    if rewrote_offset_arg:
        replace(tokens, i, src="timezone")

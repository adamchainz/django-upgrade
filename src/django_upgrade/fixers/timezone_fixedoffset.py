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
    find,
    insert,
    insert_after,
    parse_call_args,
    replace,
    update_imports,
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
    if node.level != 0 or node.module != MODULE:
        return

    if any(alias.name == OLD_NAME for alias in node.names):
        yield ast_start_offset(node), partial(
            update_imports, node=node, name_map={"FixedOffset": ""}
        )
        yield ast_start_offset(node), partial(
            insert,
            new_src="from datetime import timedelta, timezone\n",
        )


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

        # rewriting_offset_arg = False
        # if len(node.args) >= 1 and not isinstance(node.args[0], ast.Starred):
        #     yield ast_start_offset(node.args[0]), partial(
        #         insert, new_src="timedelta(minutes="
        #     )
        #     yield ast_end_offset(node.args[0]), partial(insert, new_src=")")
        #     rewriting_offset_arg = True
        # else:
        #     for keyword in node.keywords:
        #         if keyword.arg == "offset":
        #             yield ast_start_offset(keyword), partial(
        #                 insert_after,
        #                 name=OP,
        #                 src="=",
        #                 new_src="timedelta(minutes=",
        #             )
        #             yield ast_end_offset(keyword), partial(insert, new_src=")")
        #             rewriting_offset_arg = True

        # if rewriting_offset_arg:
        #     yield ast_start_offset(node), partial(replace, src="timezone")


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
                insert_after(
                    tokens, start_idx, name=OP, src="=", new_src="timedelta(minutes="
                )
                rewrote_offset_arg = True

    if rewrote_offset_arg:
        replace(tokens, i, src="timezone")

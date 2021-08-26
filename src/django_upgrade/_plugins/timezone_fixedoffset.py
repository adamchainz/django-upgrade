"""
Rewrite django.utils.timezone.FixedOffset to datetime.timezone.
https://docs.djangoproject.com/en/2.2/releases/2.2/#features-deprecated-in-2-2
"""
import ast
from functools import partial
from typing import Iterable, Tuple

from tokenize_rt import Offset

from django_upgrade._ast_helpers import ast_end_offset, ast_start_offset
from django_upgrade._data import Plugin, State, TokenFunc
from django_upgrade._token_helpers import (
    OP,
    erase_from_import_name,
    erase_node,
    insert,
    insert_after,
    replace,
)

plugin = Plugin(
    __name__,
    min_version=(2, 2),
)

MODULE = "django.utils.timezone"
OLD_NAME = "FixedOffset"


@plugin.register(ast.ImportFrom)
def visit_ImportFrom(
    state: State,
    node: ast.ImportFrom,
    parent: ast.AST,
) -> Iterable[Tuple[Offset, TokenFunc]]:
    if node.level != 0 or node.module != MODULE:
        return

    if any(alias.name == OLD_NAME for alias in node.names):
        if len(node.names) == 1:
            yield ast_start_offset(node), partial(erase_node, node=node)
        else:
            yield ast_start_offset(node), partial(
                erase_from_import_name,
                names=node.names,
                to_erase=OLD_NAME,
            )

        yield ast_start_offset(node), partial(
            insert,
            new_src="from datetime import timedelta, timezone\n",
        )


@plugin.register(ast.Call)
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
        yield ast_start_offset(node), partial(replace, src="timezone")

        if len(node.args) >= 1:
            yield ast_start_offset(node.args[0]), partial(
                insert, new_src="timedelta(minutes="
            )
            yield ast_end_offset(node.args[0]), partial(insert, new_src=")")
        else:
            for keyword in node.keywords:
                print(ast.dump(keyword))
                if keyword.arg == "offset":
                    yield ast_start_offset(keyword), partial(
                        insert_after,
                        name=OP,
                        src="=",
                        new_src="timedelta(minutes=",
                    )
                    yield ast_end_offset(keyword), partial(insert, new_src=")")

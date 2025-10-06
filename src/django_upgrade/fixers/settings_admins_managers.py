"""
Rewrite the ADMINS and MANAGERS settings to change lists of tuples to lists of strings:
https://docs.djangoproject.com/en/6.0/releases/6.0/#positional-arguments-in-django-core-mail-apis:~:text=Setting%20ADMINS%20or%20MANAGERS
"""

from __future__ import annotations

import ast
from collections.abc import Iterable
from functools import partial

from tokenize_rt import Offset, Token

from django_upgrade.ast import ast_start_offset
from django_upgrade.data import Fixer, State, TokenFunc
from django_upgrade.tokens import find_first_token, find_last_token

fixer = Fixer(
    __name__,
    min_version=(6, 0),
    condition=lambda state: state.looks_like_settings_file,
)


@fixer.register(ast.Assign)
def visit_Assign(
    state: State,
    node: ast.Assign,
    parents: tuple[ast.AST, ...],
) -> Iterable[tuple[Offset, TokenFunc]]:
    if (
        len(node.targets) == 1
        and isinstance(node.targets[0], ast.Name)
        and node.targets[0].id in ("ADMINS", "MANAGERS")
        and isinstance(node.value, (ast.List, ast.Tuple))
        and all(
            isinstance(elt, ast.Tuple) and len(elt.elts) == 2 for elt in node.value.elts
        )
        and (
            isinstance(parents[-1], ast.Module)
            or (
                isinstance(parents[-1], ast.ClassDef)
                and len(parents[-1].body) > 1
                and isinstance(parents[-2], ast.Module)
            )
        )
    ):
        yield ast_start_offset(node), partial(update_setting, node=node)


def update_setting(
    tokens: list[Token],
    i: int,
    *,
    node: ast.Assign,
) -> None:
    assert isinstance(node.value, (ast.List, ast.Tuple))

    indexes = []
    j = i
    for elt in node.value.elts:
        tuple_start = find_first_token(tokens, j, node=elt)
        tuple_end = find_last_token(tokens, tuple_start, node=elt)

        assert isinstance(elt, ast.Tuple) and len(elt.elts) == 2
        address = elt.elts[1]
        address_start = find_first_token(tokens, tuple_start, node=address)
        address_end = find_last_token(tokens, address_start, node=address)

        indexes.append((tuple_start, tuple_end, address_start, address_end))

        j = tuple_end + 1

    for tuple_start, tuple_end, address_start, address_end in reversed(indexes):
        # Replace the entire tuple with just the email address
        tokens[tuple_start : tuple_end + 1] = tokens[address_start : address_end + 1]

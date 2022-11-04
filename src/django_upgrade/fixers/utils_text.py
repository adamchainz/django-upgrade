"""
Replace imports from django.utils.translation:
https://docs.djangoproject.com/en/3.0/releases/3.0/#features-deprecated-in-3-0
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
from django_upgrade.tokens import extract_indent
from django_upgrade.tokens import find_and_replace_name
from django_upgrade.tokens import insert
from django_upgrade.tokens import update_import_names

fixer = Fixer(
    __name__,
    min_version=(3, 0),
)

MODULE = "django.utils.text"
OLD_NAME = "unescape_entities"
NAME_MAP = {
    "unescape_entities": "",
}


@fixer.register(ast.ImportFrom)
def visit_ImportFrom(
    state: State,
    node: ast.ImportFrom,
    parents: list[ast.AST],
) -> Iterable[tuple[Offset, TokenFunc]]:
    if (
        node.level == 0
        and node.module == MODULE
        and any(
            (alias.name == OLD_NAME and alias.asname is None) for alias in node.names
        )
    ):
        yield ast_start_offset(node), partial(fix_import, node=node)


def fix_import(tokens: list[Token], i: int, *, node: ast.ImportFrom) -> None:
    j, indent = extract_indent(tokens, i)
    update_import_names(tokens, i, node=node, name_map={OLD_NAME: ""})
    insert(tokens, j, new_src=f"{indent}import html\n")


@fixer.register(ast.Name)
def visit_Name(
    state: State,
    node: ast.Name,
    parents: list[ast.AST],
) -> Iterable[tuple[Offset, TokenFunc]]:
    if node.id == OLD_NAME and OLD_NAME in state.from_imports[MODULE]:
        yield ast_start_offset(node), partial(
            find_and_replace_name, name=OLD_NAME, new="html.escape"
        )

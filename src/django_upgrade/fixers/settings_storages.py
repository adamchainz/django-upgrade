"""
Merge DEFAULT_FILE_STORAGE and STATICFILES_STORAGE into new STORAGES setting:
https://docs.djangoproject.com/en/4.2/releases/4.2/#custom-file-storages
"""
from __future__ import annotations

import ast
from functools import partial
from typing import Iterable
from typing import MutableMapping
from weakref import WeakKeyDictionary

from tokenize_rt import Offset
from tokenize_rt import Token

from django_upgrade.ast import ast_start_offset
from django_upgrade.data import Fixer
from django_upgrade.data import State
from django_upgrade.data import TokenFunc
from django_upgrade.tokens import erase_node
from django_upgrade.tokens import find
from django_upgrade.tokens import insert
from django_upgrade.tokens import STRING

fixer = Fixer(
    __name__,
    min_version=(4, 2),
)

# Keep track of seen assignments

NAME_MAP = {
    "DEFAULT_FILE_STORAGE": "default",
    "STATICFILES_STORAGE": "staticfiles",
}


class SettingsDetails:
    __slots__ = (
        "all_rewritable",
        "nodes",
        "value_tokens",
        "rewritten",
        "settings_star_import",
    )

    def __init__(self) -> None:
        self.all_rewritable = True
        self.nodes: dict[str, ast.Assign] = {}
        self.value_tokens: dict[str, Token] = {}
        self.rewritten: dict[str, bool] = {}
        self.settings_star_import = False


settings_details: MutableMapping[State, SettingsDetails] = WeakKeyDictionary()


@fixer.register(ast.ImportFrom)
def visit_ImportFrom(
    state: State,
    node: ast.ImportFrom,
    parents: list[ast.AST],
) -> Iterable[tuple[Offset, TokenFunc]]:
    if (
        node.names[0].name == "*"
        and node.module is not None
        and "settings" in node.module
    ):
        details = settings_details.setdefault(state, SettingsDetails())
        details.settings_star_import = True

    return ()


@fixer.register(ast.Assign)
def visit_Assign(
    state: State,
    node: ast.Assign,
    parents: list[ast.AST],
) -> Iterable[tuple[Offset, TokenFunc]]:
    if (
        state.looks_like_settings_file
        and len(node.targets) == 1
        and isinstance(node.targets[0], ast.Name)
        and (
            (name := node.targets[0].id)
            in ("DEFAULT_FILE_STORAGE", "STATICFILES_STORAGE", "STORAGES")
        )
    ):
        details = settings_details.setdefault(state, SettingsDetails())
        is_rewritable = (
            name != "STORAGES"
            and isinstance(parents[-1], ast.Module)
            and isinstance(node.value, ast.Constant)
            and isinstance(node.value.value, str)
            and name not in details.nodes
        )
        if details.all_rewritable:
            if not is_rewritable:
                details.all_rewritable = False
            else:
                details.nodes[name] = node

                yield ast_start_offset(node), partial(
                    replace_storages, details=details, name=name, node=node
                )


def replace_storages(
    tokens: list[Token],
    i: int,
    *,
    details: SettingsDetails,
    name: str,
    node: ast.Assign,
) -> None:
    if not details.all_rewritable:
        return

    details.value_tokens[name] = tokens[find(tokens, i, name=STRING)]
    details.rewritten[name] = True

    erase_node(tokens, i, node=node)
    if len(details.rewritten) == len(details.nodes):
        # We just deleted the first in the file, insert the new setting
        src_fragments = ["STORAGES = {"]
        if details.settings_star_import:
            src_fragments.append("    **STORAGES,")

        for name in NAME_MAP:
            if name in details.value_tokens:
                new_name = NAME_MAP[name]
                value_token = details.value_tokens[name]
                src_fragments.extend(
                    [
                        f'    "{new_name}": {{',
                        f'        "BACKEND": {value_token.src},',
                        "    },",
                    ]
                )
        src_fragments.append("}\n")
        insert(tokens, i, new_src="\n".join(src_fragments))

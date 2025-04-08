"""
Merge DEFAULT_FILE_STORAGE and STATICFILES_STORAGE into new STORAGES setting:
https://docs.djangoproject.com/en/4.2/releases/4.2/#custom-file-storages
"""

from __future__ import annotations

import ast
from collections.abc import Iterable
from collections.abc import MutableMapping
from functools import partial
from weakref import WeakKeyDictionary

from tokenize_rt import Offset
from tokenize_rt import Token

from django_upgrade.ast import ast_start_offset
from django_upgrade.data import Fixer
from django_upgrade.data import State
from django_upgrade.data import TokenFunc
from django_upgrade.tokens import STRING
from django_upgrade.tokens import erase_node
from django_upgrade.tokens import find
from django_upgrade.tokens import insert

fixer = Fixer(
    __name__,
    min_version=(4, 2),
    condition=lambda state: state.looks_like_settings_file,
)

# Keep track of seen assignments

NAME_MAP = {
    "DEFAULT_FILE_STORAGE": "default",
    "STATICFILES_STORAGE": "staticfiles",
}
# Keep initial values from Django if one isn't defined
INITIAL_VALUES = {
    "default": "django.core.files.storage.FileSystemStorage",
    "staticfiles": "django.contrib.staticfiles.storage.StaticFilesStorage",
}


class SettingsDetails:
    __slots__ = (
        "all_rewritable",
        "nodes",
        "value_tokens",
        "rewritten",
        "settings_star_import",
        "contexts",
    )

    def __init__(self) -> None:
        self.all_rewritable = True
        self.nodes: dict[str, ast.Assign] = {}
        self.value_tokens: dict[str, Token] = {}
        self.rewritten: dict[str, bool] = {}
        self.settings_star_import = False
        self.contexts: dict[str, tuple[ast.AST, ...]] = {}


settings_details: MutableMapping[State, SettingsDetails] = WeakKeyDictionary()


@fixer.register(ast.ImportFrom)
def visit_ImportFrom(
    state: State,
    node: ast.ImportFrom,
    parents: tuple[ast.AST, ...],
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
    parents: tuple[ast.AST, ...],
) -> Iterable[tuple[Offset, TokenFunc]]:
    if (
        len(node.targets) == 1
        and isinstance(node.targets[0], ast.Name)
        and (
            (name := node.targets[0].id)
            in ("DEFAULT_FILE_STORAGE", "STATICFILES_STORAGE", "STORAGES")
        )
    ):
        details = settings_details.setdefault(state, SettingsDetails())
        is_rewritable = (
            name != "STORAGES"
            and (
                isinstance(parents[-1], ast.Module)
                or isinstance(parents[-1], ast.ClassDef)
            )
            and isinstance(node.value, ast.Constant)
            and isinstance(node.value.value, str)
            and name not in details.nodes
        )
        if details.all_rewritable:
            if not is_rewritable:
                details.all_rewritable = False
            else:
                details.nodes[name] = node
                details.contexts[name] = parents

                yield (
                    ast_start_offset(node),
                    partial(replace_storages, details=details, name=name, node=node),
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
        context = details.contexts[name]

        is_class_based = any(isinstance(parent, ast.ClassDef) for parent in context)
        indentation = "    " if is_class_based else ""

        # We just deleted the first in the file, insert the new setting
        src_fragments = [f"{indentation}STORAGES = {{"]
        if details.settings_star_import:
            src_fragments.append(f"{indentation}    **STORAGES,")

        for name in NAME_MAP:
            if name in details.value_tokens:
                new_name = NAME_MAP[name]
                value_token = details.value_tokens[name]
                src_fragments.extend(
                    [
                        f'{indentation}    "{new_name}": {{',
                        f'{indentation}        "BACKEND": {value_token.src},',
                        f"{indentation}    }},",
                    ]
                )
            elif not details.settings_star_import:
                new_name = NAME_MAP[name]
                initial_value = INITIAL_VALUES[new_name]
                src_fragments.extend(
                    [
                        f'{indentation}    "{new_name}": {{',
                        f'{indentation}        "BACKEND": "{initial_value}",',
                        f"{indentation}    }},",
                    ]
                )

        src_fragments.append(f"{indentation}}}\n")
        insert(tokens, i, new_src="\n".join(src_fragments))

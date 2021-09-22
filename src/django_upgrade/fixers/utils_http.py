"""
Replace imports from django.utils.http:
https://docs.djangoproject.com/en/3.0/releases/3.0/#features-deprecated-in-3-0
"""
import ast
from functools import partial
from typing import Dict, Iterable, List, Optional, Tuple

from tokenize_rt import Offset, Token

from django_upgrade.ast import ast_start_offset, is_rewritable_import_from
from django_upgrade.data import Fixer, State, TokenFunc
from django_upgrade.tokens import (
    extract_indent,
    find_and_replace_name,
    insert,
    update_import_names,
)

fixer = Fixer(
    __name__,
    min_version=(3, 0),
)

MODULE = "django.utils.http"
RENAMES = {
    "is_safe_url": "url_has_allowed_host_and_scheme",
}
URLLIB_NAMES = {
    "urlquote": "quote",
    "urlquote_plus": "quote_plus",
    "urlunquote": "unquote",
    "urlunquote_plus": "unquote_plus",
}


@fixer.register(ast.ImportFrom)
def visit_ImportFrom(
    state: State,
    node: ast.ImportFrom,
    parent: ast.AST,
) -> Iterable[Tuple[Offset, TokenFunc]]:
    if node.module == MODULE and is_rewritable_import_from(node):
        name_map = {}
        urllib_names = {}
        for alias in node.names:
            if alias.name in RENAMES:
                name_map[alias.name] = RENAMES[alias.name]
            elif alias.name in URLLIB_NAMES:
                name_map[alias.name] = ""
                urllib_names[alias.name] = alias.asname

        if name_map:
            yield ast_start_offset(node), partial(
                fix_import,
                node=node,
                name_map=name_map,
                urllib_names=urllib_names,
            )


def fix_import(
    tokens: List[Token],
    i: int,
    *,
    node: ast.ImportFrom,
    name_map: Dict[str, str],
    urllib_names: Dict[str, Optional[str]],
) -> None:
    j, indent = extract_indent(tokens, i)

    update_import_names(tokens, i, node=node, name_map=name_map)

    if urllib_names:
        urllib_imports = []
        for name, asname in urllib_names.items():
            if asname is None:
                urllib_imports.append(URLLIB_NAMES[name])
            else:
                urllib_imports.append(f"{URLLIB_NAMES[name]} as {asname}")

        insert(
            tokens,
            j,
            new_src=f"{indent}from urllib.parse import {', '.join(urllib_imports)}\n",
        )


@fixer.register(ast.Name)
def visit_Name(
    state: State,
    node: ast.Name,
    parent: ast.AST,
) -> Iterable[Tuple[Offset, TokenFunc]]:
    if (name := node.id) in state.from_imports[MODULE]:
        new_name: Optional[str]
        if name in RENAMES:
            new_name = RENAMES[name]
        elif name in URLLIB_NAMES:
            new_name = URLLIB_NAMES[name]
        else:
            new_name = None

        if new_name is not None:
            yield ast_start_offset(node), partial(
                find_and_replace_name, name=name, new=new_name
            )

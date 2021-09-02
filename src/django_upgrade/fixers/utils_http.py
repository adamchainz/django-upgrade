"""
Replace imports from django.utils.http:
https://docs.djangoproject.com/en/3.0/releases/3.0/#django-utils-encoding-force-text-and-smart-text  # noqa: B950
"""
import ast
from functools import partial
from typing import Iterable, Tuple

from tokenize_rt import Offset

from django_upgrade.ast import ast_start_offset
from django_upgrade.data import Fixer, State, TokenFunc
from django_upgrade.tokens import find_and_replace_name, insert, update_imports

fixer = Fixer(
    __name__,
    min_version=(3, 0),
)

MODULE = "django.utils.http"
NAMES = {
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
    if node.level == 0 and node.module == MODULE:
        erase = {}
        add = {}
        for alias in node.names:
            if alias.name in NAMES:
                erase[alias.name] = ""
                add[alias.name] = alias.asname

        if erase:
            yield ast_start_offset(node), partial(
                update_imports, node=node, name_map=erase
            )

            imports = []
            for name, asname in add.items():
                if asname is None:
                    imports.append(NAMES[name])
                else:
                    imports.append(f"{NAMES[name]} as {asname}")

            new_import = f"from urllib.parse import {', '.join(imports)}\n"
            yield ast_start_offset(node), partial(
                insert,
                new_src=new_import,
            )


@fixer.register(ast.Name)
def visit_Name(
    state: State,
    node: ast.Name,
    parent: ast.AST,
) -> Iterable[Tuple[Offset, TokenFunc]]:
    if (name := node.id) in NAMES and name in state.from_imports[MODULE]:
        yield ast_start_offset(node), partial(
            find_and_replace_name, name=name, new=NAMES[name]
        )

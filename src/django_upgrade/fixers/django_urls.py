"""
Update URL definitions:
https://docs.djangoproject.com/en/2.0/releases/2.0/#simplified-url-routing-syntax
"""
import ast
from functools import partial
from typing import Iterable, List, MutableMapping, Optional, Set, Tuple
from weakref import WeakKeyDictionary

from tokenize_rt import Offset, Token

from django_upgrade.ast import ast_start_offset
from django_upgrade.data import Fixer, State, TokenFunc
from django_upgrade.tokens import (
    STRING,
    extract_indent,
    find,
    insert,
    replace,
    update_import_names,
)

fixer = Fixer(
    __name__,
    min_version=(2, 0),
)


@fixer.register(ast.ImportFrom)
def visit_ImportFrom(
    state: State,
    node: ast.ImportFrom,
    parent: ast.AST,
) -> Iterable[Tuple[Offset, TokenFunc]]:
    if (
        node.level == 0
        and node.module == "django.conf.urls"
        and any(
            (alias.name in ("include", "url") and alias.asname is None)
            for alias in node.names
        )
    ):
        yield ast_start_offset(node), partial(
            update_import,
            node=node,
            state=state,
        )


# Track which of path and re_path have been used for this current file
# Then when backtracking into an import statement, we can use the set of names
# to determine what names to import.
state_used_names: MutableMapping[State, Set[str]] = WeakKeyDictionary()


def update_import(
    tokens: List[Token], i: int, *, node: ast.ImportFrom, state: State
) -> None:
    """ """
    removals = set()
    additions = set()
    used_names = state_used_names.pop(state, set())

    for alias in node.names:
        if alias.asname is not None:
            continue
        if alias.name == "include":
            removals.add("include")
        elif alias.name == "url":
            removals.add("url")
            if not used_names:
                additions.add("re_path")
            else:
                additions.update(used_names)

    j, indent = extract_indent(tokens, i)
    update_import_names(
        tokens,
        i,
        node=node,
        name_map={name: "" for name in removals},
    )
    joined_names = ", ".join(sorted(additions))
    insert(
        tokens,
        j,
        new_src=f"{indent}from django.urls import {joined_names}\n",
    )


@fixer.register(ast.Call)
def visit_Call(
    state: State,
    node: ast.Call,
    parent: ast.AST,
) -> Iterable[Tuple[Offset, TokenFunc]]:
    if (
        isinstance(node.func, ast.Name)
        and node.func.id == "url"
        and "url" in state.from_imports["django.conf.urls"]
    ):
        yield ast_start_offset(node), partial(
            fix_url_call,
            node=node,
            state=state,
        )


def fix_url_call(tokens: List[Token], i: int, *, node: ast.Call, state: State) -> None:
    new_name = "re_path"
    if (
        len(node.args) >= 1
        and isinstance(node.args[0], ast.Constant)
        and isinstance(node.args[0].value, str)
    ):
        new_syntax = convert_path_syntax(node.args[0].value)
        if new_syntax is not None:
            string_idx = find(tokens, i, name=STRING)
            replace(tokens, string_idx, src=repr(new_syntax))
            new_name = "path"
    state_used_names.setdefault(state, set()).add(new_name)
    replace(tokens, i, src=new_name)


def convert_path_syntax(regex_path: str) -> Optional[str]:
    # TODO: adapt the regex -> path conversion logic from django-codemod
    if regex_path == "^$":
        return ""
    return None

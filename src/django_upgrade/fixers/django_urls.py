"""
Update URL definitions:
https://docs.djangoproject.com/en/2.0/releases/2.0/#simplified-url-routing-syntax
"""
from __future__ import annotations

import ast
import re
from functools import partial
from typing import Iterable, MutableMapping
from weakref import WeakKeyDictionary

from tokenize_rt import Offset, Token

from django_upgrade.ast import ast_start_offset, is_rewritable_import_from
from django_upgrade.compat import str_removeprefix
from django_upgrade.data import Fixer, State, TokenFunc
from django_upgrade.tokens import (
    STRING,
    erase_node,
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
) -> Iterable[tuple[Offset, TokenFunc]]:
    if (
        node.module == "django.conf.urls"
        and is_rewritable_import_from(node)
        and any(alias.name in ("include", "url") for alias in node.names)
    ):
        yield ast_start_offset(node), partial(
            update_django_conf_import,
            node=node,
            state=state,
        )
    if (
        node.module == "django.urls"
        and is_rewritable_import_from(node)
        and any(alias.name == "re_path" for alias in node.names)
    ):
        yield ast_start_offset(node), partial(
            update_django_urls_import,
            node=node,
            state=state,
        )


# Track which of path and re_path have been used for this current file
# Then when backtracking into an import statement, we can use the set of names
# to determine what names to import.
state_used_names: MutableMapping[State, set[str]] = WeakKeyDictionary()


def update_django_urls_import(
    tokens: list[Token], i: int, *, node: ast.ImportFrom, state: State
) -> None:
    used_names = state_used_names.pop(state, set())

    if used_names:
        initial_names = state.from_imports["django.urls"] - {"re_path"}
        used_names.update(initial_names)

        j, indent = extract_indent(tokens, i)
        erase_node(tokens, i, node=node)
        joined_names = ", ".join(sorted(used_names))
        insert(
            tokens,
            j,
            new_src=f"{indent}from django.urls import {joined_names}\n",
        )


def update_django_conf_import(
    tokens: list[Token], i: int, *, node: ast.ImportFrom, state: State
) -> None:
    is_concurrent = "re_path" in state.from_imports["django.urls"]
    used_names = state_used_names.pop(state, set())
    removals = set()

    for alias in node.names:
        if alias.asname is not None:
            continue
        if alias.name in ("include", "url") and (used_names or is_concurrent):
            removals.add(alias.name)

    if removals:
        j, indent = extract_indent(tokens, i)
        update_import_names(
            tokens,
            i,
            node=node,
            name_map={name: "" for name in removals},
        )
        if not is_concurrent:
            joined_names = ", ".join(sorted(used_names))
            insert(
                tokens,
                j,
                new_src=f"{indent}from django.urls import {joined_names}\n",
            )
        else:
            state_used_names[state] = used_names


@fixer.register(ast.Call)
def visit_Call(
    state: State,
    node: ast.Call,
    parent: ast.AST,
) -> Iterable[tuple[Offset, TokenFunc]]:
    if (
        isinstance(node.func, ast.Name)
        and (
            node.func.id == "url"
            and "url" in state.from_imports["django.conf.urls"]
            or node.func.id == "re_path"
            and "re_path" in state.from_imports["django.urls"]
        )
        # cannot convert where called with all kwargs as names don't align
        and len(node.args) >= 1
    ):
        regex_path: str | None = None
        if isinstance(node.args[0], ast.Constant) and isinstance(
            node.args[0].value, str
        ):
            regex_path = node.args[0].value

        yield ast_start_offset(node), partial(
            fix_url_call,
            regex_path=regex_path,
            state=state,
        )

    if (
        isinstance(node.func, ast.Name)
        and node.func.id == "include"
        and "include" in state.from_imports["django.conf.urls"]
    ):
        state_used_names.setdefault(state, set()).add("include")


def fix_url_call(
    tokens: list[Token], i: int, *, regex_path: str | None, state: State
) -> None:
    new_name = "re_path"
    if regex_path is not None:
        path = convert_path_syntax(regex_path)
        if path is not None:
            string_idx = find(tokens, i, name=STRING)
            replace(tokens, string_idx, src=repr(path))
            new_name = "path"
    state_used_names.setdefault(state, set()).add(new_name)
    replace(tokens, i, src=new_name)


REGEX_TO_CONVERTER = {
    "[0-9]+": "int",
    r"\d+": "int",
    ".+": "path",
    "[-a-zA-Z0-9_]+": "slug",
    "[^/]+": "str",
    "[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}": "uuid",
}


def convert_path_syntax(regex_path: str) -> str | None:
    if not regex_path.endswith("$"):
        return None
    remaining = str_removeprefix(regex_path[:-1], "^")
    path = ""
    while "(?P<" in remaining:
        prefix, rest = remaining.split("(?P<", 1)
        group, remaining = rest.split(")", 1)
        group_name, group_regex = group.split(">", 1)
        try:
            converter = REGEX_TO_CONVERTER[group_regex]
        except KeyError:
            return None

        path += prefix
        path += f"<{converter}:{group_name}>"

    path += remaining

    dashless_path = path.replace("-", "")
    if re.escape(dashless_path) != dashless_path:
        # path still contains regex special characters
        # dashes are ignored as they only have meaning in regexes within []
        return None

    return path

"""
Update URL definitions:
https://docs.djangoproject.com/en/2.0/releases/2.0/#simplified-url-routing-syntax
"""
from __future__ import annotations

import ast
import re
from functools import partial
from typing import Iterable
from typing import MutableMapping
from weakref import WeakKeyDictionary

from tokenize_rt import Offset
from tokenize_rt import Token

from django_upgrade.ast import ast_start_offset
from django_upgrade.ast import is_rewritable_import_from
from django_upgrade.compat import str_removeprefix
from django_upgrade.compat import str_removesuffix
from django_upgrade.data import Fixer
from django_upgrade.data import State
from django_upgrade.data import TokenFunc
from django_upgrade.tokens import extract_indent
from django_upgrade.tokens import find
from django_upgrade.tokens import insert
from django_upgrade.tokens import replace
from django_upgrade.tokens import str_repr_matching
from django_upgrade.tokens import STRING
from django_upgrade.tokens import update_import_names

fixer = Fixer(
    __name__,
    min_version=(2, 0),
)


@fixer.register(ast.ImportFrom)
def visit_ImportFrom(
    state: State,
    node: ast.ImportFrom,
    parents: list[ast.AST],
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
    elif (
        node.module == "django.urls"
        and is_rewritable_import_from(node)
        and any(alias.name == "re_path" for alias in node.names)
    ):
        yield ast_start_offset(node), partial(
            update_django_urls_import,
            node=node,
            state=state,
        )


# Track if re_path has been used, and which names need adding.
# When fixing import statements, these variables determine which names to
# import/remove.
state_re_path_used: MutableMapping[State, bool] = WeakKeyDictionary()
state_added_names: MutableMapping[State, set[str]] = WeakKeyDictionary()


def update_django_conf_import(
    tokens: list[Token], i: int, *, node: ast.ImportFrom, state: State
) -> None:
    re_path_imported = "re_path" in state.from_imports["django.urls"]
    added_names = state_added_names.pop(state, set())
    removals = set()

    for alias in node.names:
        if alias.asname is not None:
            continue
        if alias.name in ("include", "url") and (added_names or re_path_imported):
            removals.add(alias.name)

    if removals:
        j, indent = extract_indent(tokens, i)
        update_import_names(
            tokens,
            i,
            node=node,
            name_map={name: "" for name in removals},
        )
        if not re_path_imported:
            joined_names = ", ".join(sorted(added_names))
            insert(
                tokens,
                j,
                new_src=f"{indent}from django.urls import {joined_names}\n",
            )
        else:
            state_added_names[state] = added_names


def update_django_urls_import(
    tokens: list[Token], i: int, *, node: ast.ImportFrom, state: State
) -> None:
    re_path_used = state_re_path_used.get(state, False)
    added_names = state_added_names.pop(state, set())
    missing_names = added_names - state.from_imports["django.urls"]

    if (
        added_names
        and not re_path_used
        and "re_path" in state.from_imports["django.urls"]
    ):
        update_import_names(
            tokens,
            i,
            node=node,
            name_map={"re_path": ""},
        )

    if missing_names:
        j, indent = extract_indent(tokens, i)
        joined_names = ", ".join(sorted(missing_names))
        insert(
            tokens,
            j,
            new_src=f"{indent}from django.urls import {joined_names}\n",
        )


@fixer.register(ast.Call)
def visit_Call(
    state: State,
    node: ast.Call,
    parents: list[ast.AST],
) -> Iterable[tuple[Offset, TokenFunc]]:
    if isinstance(node.func, ast.Name):
        if (
            (
                (
                    (node_name := node.func.id) == "url"
                    and "url" in state.from_imports["django.conf.urls"]
                )
                or (
                    (node_name := node.func.id) == "re_path"
                    and "re_path" in state.from_imports["django.urls"]
                )
            )
            # cannot convert where called with all kwargs as names don't align
            and len(node.args) >= 1
        ):
            regex_path: str | None = None
            if isinstance(node.args[0], ast.Constant) and isinstance(
                node.args[0].value, str
            ):
                regex_path = node.args[0].value

            include_called = (
                len(node.args) >= 2
                and isinstance(node.args[1], ast.Call)
                and isinstance(node.args[1].func, ast.Name)
                and node.args[1].func.id == "include"
            )
            yield ast_start_offset(node), partial(
                fix_url_call,
                regex_path=regex_path,
                state=state,
                node_name=node_name,
                include_called=include_called,
            )

        elif (
            node.func.id == "include"
            and "include" in state.from_imports["django.conf.urls"]
        ):
            state_added_names.setdefault(state, set()).add("include")


def fix_url_call(
    tokens: list[Token],
    i: int,
    *,
    regex_path: str | None,
    state: State,
    node_name: str,
    include_called: bool,
) -> None:
    new_name = "re_path"
    if regex_path is not None:
        path = convert_path_syntax(regex_path, include_called)
        if path is not None:
            string_idx = find(tokens, i, name=STRING)
            path = str_repr_matching(path, match_quotes=tokens[string_idx].src)
            replace(tokens, string_idx, src=path)
            new_name = "path"
    if new_name != node_name:
        state_added_names.setdefault(state, set()).add(new_name)
        replace(tokens, i, src=new_name)
    else:
        state_re_path_used.setdefault(state, True)


REGEX_TO_CONVERTER = {
    "[0-9]+": "int",
    r"\d+": "int",
    ".+": "path",
    "[-a-zA-Z0-9_]+": "slug",
    "[^/]+": "str",
    "[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}": "uuid",
}


def convert_path_syntax(regex_path: str, include_called: bool) -> str | None:
    if not (regex_path.endswith("$") or include_called):
        return None
    remaining = str_removeprefix(regex_path, "^")
    remaining = str_removesuffix(remaining, "$")
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

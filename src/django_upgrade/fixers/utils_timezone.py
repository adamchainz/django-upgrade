"""
Replace django.utils.timezone.utc with datetime.timezone.utc
https://docs.djangoproject.com/en/4.1/releases/4.1/#id2
"""
from __future__ import annotations

import ast
from functools import partial
from typing import Iterable, MutableMapping
from weakref import WeakKeyDictionary

from tokenize_rt import Offset, Token

from django_upgrade.ast import ast_start_offset, is_rewritable_import_from
from django_upgrade.data import Fixer, State, TokenFunc
from django_upgrade.tokens import (
    LOGICAL_NEWLINE,
    find,
    find_last_token,
    insert,
    replace,
    update_import_names,
)

fixer = Fixer(
    __name__,
    min_version=(4, 1),
)


@fixer.register(ast.Name)
def visit_Name(
    state: State,
    node: ast.Name,
    parents: list[ast.AST],
) -> Iterable[tuple[Offset, TokenFunc]]:
    if node.id == "utc" and (
        (details := get_import_details(state, parents[0])).old_utc_import is not None
    ):
        yield from maybe_rewrite_import(details)
        if details.datetime_module:
            new_src = f"{details.datetime_module}.timezone.utc"
        else:
            new_src = "timezone.utc"
        yield ast_start_offset(node), partial(replace, src=new_src)


@fixer.register(ast.Attribute)
def visit_Attribute(
    state: State,
    node: ast.Attribute,
    parents: list[ast.AST],
) -> Iterable[tuple[Offset, TokenFunc]]:
    if (
        node.attr == "utc"
        and isinstance(node.value, ast.Name)
        and node.value.id == "timezone"
        and (
            (details := get_import_details(state, parents[0])).old_timezone_import
            is not None
        )
    ):
        yield from maybe_rewrite_import(details)
        if details.datetime_module:
            new_src = f"{details.datetime_module}.timezone"
            yield ast_start_offset(node), partial(replace, src=new_src)


class ImportDetails:
    def __init__(self) -> None:
        self.first_import: ast.Import | ast.ImportFrom | None = None
        self.old_utc_import: ast.ImportFrom | None = None
        self.old_timezone_import: ast.ImportFrom | None = None
        self.from_datetime_import: ast.ImportFrom | None = None
        self.datetime_module: str | None = None
        self.rewrite_scheduled = False


modules: MutableMapping[State, ImportDetails] = WeakKeyDictionary()


def get_import_details(state: State, module: ast.AST) -> ImportDetails:
    assert isinstance(module, ast.Module)
    try:
        return modules[state]
    except KeyError:
        pass

    details = ImportDetails()

    for node in module.body:
        if (
            isinstance(node, ast.Expr)
            and isinstance(node.value, ast.Constant)
            and isinstance(node.value.value, str)
        ):
            # docstring
            continue
        elif isinstance(node, ast.Import):
            if details.first_import is None:
                details.first_import = node

            for alias in node.names:
                if alias.name == "datetime":
                    if alias.asname is None:
                        details.datetime_module = "datetime"
                    else:
                        details.datetime_module = alias.asname

        elif isinstance(node, ast.ImportFrom):
            if details.first_import is None:
                details.first_import = node

            if is_rewritable_import_from(node):
                if node.module == "django.utils.timezone" and any(
                    a.name == "utc" for a in node.names
                ):
                    details.old_utc_import = node
                elif node.module == "django.utils" and any(
                    a.name == "timezone" for a in node.names
                ):
                    details.old_timezone_import = node
                elif node.module == "datetime":
                    details.from_datetime_import = node
        else:
            break

    modules[state] = details
    return details


def maybe_rewrite_import(
    details: ImportDetails,
) -> Iterable[tuple[Offset, TokenFunc]]:
    if details.rewrite_scheduled:
        return

    if details.old_utc_import is not None:
        yield ast_start_offset(details.old_utc_import), partial(
            update_import_names,
            node=details.old_utc_import,
            name_map={"utc": ""},
        )
    else:
        assert details.old_timezone_import is not None
        yield ast_start_offset(details.old_timezone_import), partial(
            update_import_names,
            node=details.old_timezone_import,
            name_map={"timezone": ""},
        )

    if details.from_datetime_import is not None:
        yield ast_start_offset(details.from_datetime_import), partial(
            add_timezone_to_from, node=details.from_datetime_import
        )
    elif not details.datetime_module:
        assert details.first_import is not None
        yield ast_start_offset(details.first_import), partial(
            add_new_timezone_import,
            node=details.first_import,
        )

    details.rewrite_scheduled = True


def add_timezone_to_from(tokens: list[Token], i: int, *, node: ast.ImportFrom) -> None:
    j = find_last_token(tokens, i, node=node)
    insert(tokens, j + 1, new_src=", timezone")


def add_new_timezone_import(
    tokens: list[Token], i: int, *, node: ast.Import | ast.ImportFrom
) -> None:
    new_src = "from datetime import timezone\n"
    if isinstance(node, ast.ImportFrom) and node.module == "__future__":
        # insert after
        j = find_last_token(tokens, i, node=node)
        j = find(tokens, i, name=LOGICAL_NEWLINE)
        insert(tokens, j + 1, new_src=new_src)
    else:
        insert(tokens, i, new_src=new_src)

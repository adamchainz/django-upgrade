"""
Replace django.utils.timezone.utc with datetime.timezone.utc
https://docs.djangoproject.com/en/4.1/releases/4.1/#id2
"""

from __future__ import annotations

import ast
from collections.abc import Iterable, MutableMapping
from functools import partial
from weakref import WeakKeyDictionary

from tokenize_rt import Offset, Token

from django_upgrade.ast import (
    ast_start_offset,
    get_module_names,
    is_rewritable_import_from,
)
from django_upgrade.data import Fixer, State, TokenFunc
from django_upgrade.tokens import (
    extract_indent,
    find_first_token,
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
    parents: tuple[ast.AST, ...],
) -> Iterable[tuple[Offset, TokenFunc]]:
    if (
        node.id == "utc"
        and (
            (details := get_import_details(state, parents[0])).old_utc_import
            is not None
        )
        and details.datetime_module is not None
    ):
        yield from maybe_rewrite_imports(details, erase=True)
        new_src = f"{details.datetime_module}.timezone.utc"
        yield ast_start_offset(node), partial(replace, src=new_src)


@fixer.register(ast.Attribute)
def visit_Attribute(
    state: State,
    node: ast.Attribute,
    parents: tuple[ast.AST, ...],
) -> Iterable[tuple[Offset, TokenFunc]]:
    if (
        node.attr == "utc"
        and isinstance(node.value, ast.Name)
        and node.value.id == "timezone"
        and "timezone" in state.from_imports["django.utils"]
        and (details := get_import_details(state, parents[0])).datetime_module
        is not None
    ):
        yield from maybe_rewrite_imports(details, erase=False)
        new_src = f"{details.datetime_module}.timezone"
        yield ast_start_offset(node), partial(replace, src=new_src)


class ImportDetails:
    __slots__ = (
        "old_utc_import",
        "datetime_module",
        "rewrite_scheduled",
        "first_import_node",
        "needs_datetime_import",
        "add_import_scheduled",
    )

    def __init__(self) -> None:
        self.old_utc_import: ast.ImportFrom | None = None
        self.datetime_module: str | None = None
        self.rewrite_scheduled = False
        self.first_import_node: ast.Import | ast.ImportFrom | None = None
        self.needs_datetime_import = False
        self.add_import_scheduled = False


import_details: MutableMapping[State, ImportDetails] = WeakKeyDictionary()


def get_import_details(state: State, module: ast.AST) -> ImportDetails:
    assert isinstance(module, ast.Module)
    try:
        return import_details[state]
    except KeyError:
        pass

    details = ImportDetails()

    for node in module.body:  # pragma: no branch
        if (
            isinstance(node, ast.Expr)
            and isinstance(node.value, ast.Constant)
            and isinstance(node.value.value, str)
        ):
            # docstring
            continue

        if not isinstance(node, (ast.Import, ast.ImportFrom)):
            break

        if isinstance(node, ast.ImportFrom) and node.module == "__future__":
            continue

        if details.first_import_node is None:
            details.first_import_node = node

        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name == "datetime":
                    if alias.asname is None:
                        details.datetime_module = "datetime"
                    else:
                        details.datetime_module = alias.asname

        # coverage bug
        # https://github.com/nedbat/coveragepy/issues/1333
        elif (  # pragma: no cover
            is_rewritable_import_from(node)
            and node.module == "django.utils.timezone"
            and any(a.name == "utc" for a in node.names)
        ):
            details.old_utc_import = node

    if (
        details.datetime_module is None
        and details.first_import_node is not None
        and "dt" not in get_module_names(module)
    ):
        details.datetime_module = "dt"
        details.needs_datetime_import = True

    import_details[state] = details
    return details


def maybe_rewrite_imports(
    details: ImportDetails,
    *,
    erase: bool,
) -> Iterable[tuple[Offset, TokenFunc]]:
    do_insert = details.needs_datetime_import and not details.add_import_scheduled
    do_erase = erase and not details.rewrite_scheduled

    if not do_insert and not do_erase:
        return

    assert details.first_import_node is not None
    yield (
        ast_start_offset(details.first_import_node),
        partial(
            rewrite_imports,
            node=details.old_utc_import,
            insert_dt=do_insert,
            erase_utc=do_erase,
        ),
    )

    if do_insert:
        details.add_import_scheduled = True
    if do_erase:
        details.rewrite_scheduled = True


def rewrite_imports(
    tokens: list[Token],
    i: int,
    *,
    node: ast.ImportFrom | None,
    insert_dt: bool,
    erase_utc: bool,
) -> None:
    if insert_dt:
        j, indent = extract_indent(tokens, i)
        insert(tokens, j, new_src=f"{indent}import datetime as dt\n")
        i += 1
    if erase_utc:
        assert node is not None
        i = find_first_token(tokens, i, node=node)
        update_import_names(tokens, i, node=node, name_map={"utc": ""})

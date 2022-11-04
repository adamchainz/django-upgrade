"""
Replace django.utils.timezone.utc with datetime.timezone.utc
https://docs.djangoproject.com/en/4.1/releases/4.1/#id2
"""
from __future__ import annotations

import ast
from functools import partial
from typing import Iterable
from typing import MutableMapping
from weakref import WeakKeyDictionary

from tokenize_rt import Offset

from django_upgrade.ast import ast_start_offset
from django_upgrade.ast import is_rewritable_import_from
from django_upgrade.data import Fixer
from django_upgrade.data import State
from django_upgrade.data import TokenFunc
from django_upgrade.tokens import replace
from django_upgrade.tokens import update_import_names

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
    if (
        node.id == "utc"
        and (
            (details := get_import_details(state, parents[0])).old_utc_import
            is not None
        )
        and details.datetime_module is not None
    ):
        yield from maybe_rewrite_import(details)
        new_src = f"{details.datetime_module}.timezone.utc"
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
        and "timezone" in state.from_imports["django.utils"]
        and (details := get_import_details(state, parents[0]))
        and details.datetime_module is not None
    ):
        new_src = f"{details.datetime_module}.timezone"
        yield ast_start_offset(node), partial(replace, src=new_src)


class ImportDetails:
    __slots__ = (
        "old_utc_import",
        "datetime_module",
        "rewrite_scheduled",
    )

    def __init__(self) -> None:
        self.old_utc_import: ast.ImportFrom | None = None
        self.datetime_module: str | None = None
        self.rewrite_scheduled = False


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

    import_details[state] = details
    return details


def maybe_rewrite_import(
    details: ImportDetails,
) -> Iterable[tuple[Offset, TokenFunc]]:
    if details.rewrite_scheduled:
        return

    assert details.old_utc_import is not None
    yield ast_start_offset(details.old_utc_import), partial(
        update_import_names,
        node=details.old_utc_import,
        name_map={"utc": ""},
    )

    details.rewrite_scheduled = True

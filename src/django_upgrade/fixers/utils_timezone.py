"""
Replace django.utils.timezone.utc with datetime.timezone.utc
https://docs.djangoproject.com/en/4.1/releases/4.1/#id2
"""
from __future__ import annotations

import ast
from functools import partial
from typing import Iterable, MutableMapping
from weakref import WeakKeyDictionary

from tokenize_rt import Offset

from django_upgrade.ast import ast_start_offset, is_rewritable_import_from
from django_upgrade.data import Fixer, State, TokenFunc
from django_upgrade.tokens import insert, replace, update_import_names

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


class ImportDetails:
    def __init__(self) -> None:
        self.insert_before: ast.Import | ast.ImportFrom | None = None
        self.datetime_module: str | None = None
        self.old_utc_import: ast.ImportFrom | None = None
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
        if isinstance(node, ast.Constant):
            # docstring
            continue
        elif isinstance(node, ast.Import):
            if details.insert_before is None:
                details.insert_before = node

            for alias in node.names:
                if alias.name == "datetime":
                    if alias.asname is None:
                        details.datetime_module = "datetime"
                    else:
                        details.datetime_module = alias.asname

        elif isinstance(node, ast.ImportFrom):
            if details.insert_before is None and is_rewritable_import_from(node):
                details.insert_before = node

            if node.module == "django.utils.timezone" and any(
                a.name == "utc" for a in node.names
            ):
                details.old_utc_import = node
        else:
            break

    modules[state] = details
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

    if not details.datetime_module:
        assert details.insert_before is not None
        yield ast_start_offset(details.insert_before), partial(
            insert, new_src="from datetime import timezone\n"
        )

    details.rewrite_scheduled = True

"""
Swap django.core.mail.BadHeaderError with ValueError:
https://docs.djangoproject.com/en/5.1/releases/5.1/#features-deprecated-in-5-1
"""

from __future__ import annotations

import ast
from collections.abc import Iterable, MutableMapping
from functools import partial
from weakref import WeakKeyDictionary

from tokenize_rt import Offset

from django_upgrade.ast import ast_start_offset, is_rewritable_import_from
from django_upgrade.data import Fixer, State, TokenFunc
from django_upgrade.tokens import find_and_replace_name, update_import_names

fixer = Fixer(
    __name__,
    min_version=(5, 1),
)

MODULE = "django.core.mail"
OLD_NAME = "BadHeaderError"
NEW_NAME = "ValueError"

# Track aliased imports like "from django.core.mail import BadHeaderError as BHE"
# Maps state to the set of alias names that should be replaced with ValueError
aliased_names: MutableMapping[State, set[str]] = WeakKeyDictionary()


@fixer.register(ast.ImportFrom)
def visit_ImportFrom(
    state: State,
    node: ast.ImportFrom,
    parents: tuple[ast.AST, ...],
) -> Iterable[tuple[Offset, TokenFunc]]:
    if node.module == MODULE and is_rewritable_import_from(node):
        # Check if BadHeaderError is in the imports
        aliases_to_track = set()
        for alias in node.names:
            if alias.name == OLD_NAME:
                # Track the alias name if it exists
                if alias.asname is not None:
                    aliases_to_track.add(alias.asname)
                # Remove BadHeaderError from the import
                name_map = {OLD_NAME: ""}
                if aliases_to_track:
                    # Merge with any previously recorded aliases for this state
                    existing = aliased_names.get(state)
                    if existing is None:
                        aliased_names[state] = aliases_to_track
                    else:
                        existing.update(aliases_to_track)
                yield (
                    ast_start_offset(node),
                    partial(
                        update_import_names,
                        node=node,
                        name_map=name_map,
                    ),
                )
                break


@fixer.register(ast.Name)
def visit_Name(
    state: State,
    node: ast.Name,
    parents: tuple[ast.AST, ...],
) -> Iterable[tuple[Offset, TokenFunc]]:
    # Check if this is a direct usage of BadHeaderError (unaliased import)
    if node.id == OLD_NAME and OLD_NAME in state.from_imports[MODULE]:
        yield (
            ast_start_offset(node),
            partial(find_and_replace_name, name=OLD_NAME, new=NEW_NAME),
        )
    # Check if this is an aliased usage (e.g., BHE when imported as BadHeaderError as BHE)
    elif node.id in aliased_names.get(state, set()):
        yield (
            ast_start_offset(node),
            partial(find_and_replace_name, name=node.id, new=NEW_NAME),
        )

"""
Rewrite Model.Meta.index_together declarations into Model.Meta.Index
declarations.
https://docs.djangoproject.com/en/4.2/releases/4.2/#index-together-option-is-deprecated-in-favor-of-indexes
"""

from __future__ import annotations

import ast
from functools import partial
from typing import Iterable

from tokenize_rt import Offset
from tokenize_rt import Token

from django_upgrade.ast import ast_start_offset
from django_upgrade.data import Fixer
from django_upgrade.data import State
from django_upgrade.data import TokenFunc
from django_upgrade.tokens import erase_node
from django_upgrade.tokens import find_last_token
from django_upgrade.tokens import insert

fixer = Fixer(
    __name__,
    min_version=(4, 2),
    condition=lambda state: state.looks_like_models_file,
)


@fixer.register(ast.ClassDef)
def visit_ClassDef(
    state: State,
    node: ast.ClassDef,
    parents: list[ast.AST],
) -> Iterable[tuple[Offset, TokenFunc]]:
    if node.name == "Meta" and isinstance(parents[-1], ast.ClassDef):
        # Find rewritable index_together declaration
        index_togethers: list[ast.Assign] = []
        for subnode in node.body:
            if (
                isinstance(subnode, ast.Assign)
                and len(subnode.targets) == 1
                and isinstance(subnode.targets[0], ast.Name)
                and subnode.targets[0].id == "index_together"
                and isinstance(subnode.value, (ast.Tuple, ast.List))
                and all(
                    isinstance(elt, (ast.Tuple, ast.List))
                    and all(
                        (
                            isinstance(subelt, ast.Constant)
                            and isinstance(subelt.value, str)
                        )
                        for subelt in elt.elts
                    )
                    for elt in subnode.value.elts
                )
            ):
                index_togethers.append(subnode)

        if len(index_togethers) != 1:
            return

        index_together = index_togethers[0]

        # Optionally find indexes declaration to extend
        indexeses: list[ast.Assign] = []
        for subnode in node.body:
            if (
                isinstance(subnode, ast.Assign)
                and len(subnode.targets) == 1
                and isinstance(subnode.targets[0], ast.Name)
                and subnode.targets[0].id == "indexes"
                and isinstance(subnode.value, (ast.Tuple, ast.List))
            ):
                indexeses.append(subnode)

        if len(indexeses) > 1:
            return

        try:
            indexes = indexeses[0]
        except IndexError:
            # TODO: handle none case
            # indexes = None
            return

        # TODO: actually generate this, require existing django.db.models import or 'from django.db.models import Index'
        index_src = "models.Index(fields=[...])"

        yield ast_start_offset(index_together), partial(
            remove_index_together_and_maybe_add_indexes,
            index_together=index_together,
            add_indexes=False,
            index_src=index_src,
        )
        yield ast_start_offset(indexes), partial(
            extend_indexes, indexes=indexes, index_src=index_src
        )


def remove_index_together_and_maybe_add_indexes(
    tokens: list[Token],
    i: int,
    *,
    index_together: ast.Assign,
    add_indexes: bool,
    index_src: str,
) -> None:
    if add_indexes:
        # TODO
        pass

    erase_node(tokens, i, node=index_together)


def extend_indexes(
    tokens: list[Token],
    i: int,
    *,
    indexes: ast.Assign,
    index_src: str,
) -> None:
    closing_punctuation = find_last_token(tokens, i, node=indexes.value)
    # TODO: handle case where indexes has values already with/without trailing comma
    insert(tokens, closing_punctuation, new_src=index_src)

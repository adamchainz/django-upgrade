"""
Rewrite Model.Meta.index_together declarations into Model.Meta.Index
declarations.
https://docs.djangoproject.com/en/4.2/releases/4.2/#index-together-option-is-deprecated-in-favor-of-indexes
"""

from __future__ import annotations

import ast
from functools import partial
from typing import Iterable

from tokenize_rt import UNIMPORTANT_WS
from tokenize_rt import Offset
from tokenize_rt import Token

from django_upgrade.ast import ast_start_offset
from django_upgrade.compat import str_removesuffix
from django_upgrade.data import Fixer
from django_upgrade.data import State
from django_upgrade.data import TokenFunc
from django_upgrade.tokens import DEDENT
from django_upgrade.tokens import INDENT
from django_upgrade.tokens import OP
from django_upgrade.tokens import PHYSICAL_NEWLINE
from django_upgrade.tokens import erase_node
from django_upgrade.tokens import extract_indent
from django_upgrade.tokens import find_last_token
from django_upgrade.tokens import insert
from django_upgrade.tokens import str_repr_matching

fixer = Fixer(
    __name__,
    min_version=(4, 2),
    condition=lambda state: state.looks_like_models_file,
)


@fixer.register(ast.ClassDef)
def visit_ClassDef(
    state: State,
    node: ast.ClassDef,
    parents: tuple[ast.AST, ...],
) -> Iterable[tuple[Offset, TokenFunc]]:
    if (
        node.name != "Meta"
        or sum(isinstance(p, ast.ClassDef) for p in parents[1:]) != 1
        or not all(isinstance(subnode, ast.Assign) for subnode in node.body)
    ):
        return

    # Find rewritable index_together declaration
    index_togethers: list[ast.Assign] = []
    for subnode in node.body:
        assert isinstance(subnode, ast.Assign)  # type checked above
        if (
            len(subnode.targets) == 1
            and isinstance(subnode.targets[0], ast.Name)
            and subnode.targets[0].id == "index_together"
            and isinstance(subnode.value, (ast.List, ast.Tuple))
            and (
                all(
                    (isinstance(elt, ast.Constant) and isinstance(elt.value, str))
                    for elt in subnode.value.elts
                )
                or all(
                    isinstance(elt, (ast.List, ast.Tuple))
                    and all(
                        (
                            isinstance(subelt, ast.Constant)
                            and isinstance(subelt.value, str)
                        )
                        for subelt in elt.elts
                    )
                    for elt in subnode.value.elts
                )
            )
        ):
            index_togethers.append(subnode)

    if len(index_togethers) != 1:
        return

    index_together = index_togethers[0]

    # Try to find an indexes declaration to extend
    indexeses: list[ast.Assign] = []
    for subnode in node.body:
        assert isinstance(subnode, ast.Assign)  # type checked above
        if (
            len(subnode.targets) == 1
            and isinstance(subnode.targets[0], ast.Name)
            and subnode.targets[0].id == "indexes"
            and isinstance(subnode.value, (ast.List, ast.Tuple))
        ):
            indexeses.append(subnode)

    if len(indexeses) > 1:
        return

    try:
        indexes = indexeses[0]
    except IndexError:
        indexes = None

    if "models" in state.from_imports["django.db"]:
        index_ref = "models.Index"
    elif "Index" in state.from_imports["django.db.models"]:
        index_ref = "Index"
    else:
        return

    src_chunks = []
    assert isinstance(index_together.value, (ast.List, ast.Tuple))  # type checked above
    # Single index: pretend it was a list-of-lists (or tuple-of-tuples, etc.)
    if isinstance(index_together.value.elts[0], ast.Constant):
        iterate: list[ast.List | ast.Tuple] = [
            type(index_together.value)(elts=index_together.value.elts)
        ]
    else:
        # type checked above
        iterate = index_together.value.elts  # type: ignore [assignment]
    for indexnode in iterate:
        index_src = index_ref
        index_src += "(fields="
        if isinstance(indexnode, ast.Tuple):
            index_src += "("
        else:
            index_src += "["

        assert isinstance(indexnode, (ast.List, ast.Tuple))  # type checked above
        for const in indexnode.elts:
            # type checked above:
            assert isinstance(const, ast.Constant)
            assert isinstance(const.value, str)
            # Default to double quotes because they’re fashionable
            index_src += str_repr_matching(const.value, match_quotes='"')
            index_src += ", "

        index_src = str_removesuffix(index_src, ", ")

        if isinstance(indexnode, ast.Tuple):
            index_src += ")"
        else:
            index_src += "]"

        index_src += ")"

        src_chunks.append(index_src)

    index_src = ", ".join(src_chunks)

    yield ast_start_offset(index_together), partial(
        remove_index_together_and_maybe_add_indexes,
        index_together=index_together,
        add_indexes=(indexes is None),
        index_src=index_src,
    )
    if indexes is not None:
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
    j, indent = extract_indent(tokens, i)
    erase_node(tokens, i, node=index_together)
    if add_indexes:
        insert(tokens, j, new_src=f"{indent}indexes = [{index_src}]\n")


def extend_indexes(
    tokens: list[Token],
    i: int,
    *,
    indexes: ast.Assign,
    index_src: str,
) -> None:
    assert isinstance(indexes.value, (ast.List, ast.Tuple))  # type checked above
    closing_punctuation = find_last_token(tokens, i, node=indexes.value)
    if len(indexes.value.elts) == 0 or tokens[closing_punctuation - 1].name in (
        INDENT,
        DEDENT,
        UNIMPORTANT_WS,
        PHYSICAL_NEWLINE,
    ):
        prefix = ""
    else:
        j = find_last_token(tokens, i, node=indexes.value.elts[-1])
        if any(
            t.name == OP and t.src == "," for t in tokens[j + 1 : closing_punctuation]
        ):
            prefix = " "
        else:
            prefix = ", "

    insert(tokens, closing_punctuation, new_src=f"{prefix}{index_src}")

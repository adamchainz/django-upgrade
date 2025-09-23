"""
Drop `.choices` for model field `choices` parameters:
https://docs.djangoproject.com/en/5.0/releases/5.0/#forms
"""

from __future__ import annotations

import ast
from collections import defaultdict
from collections.abc import Iterable
from functools import partial
from typing import cast
from weakref import WeakKeyDictionary

from tokenize_rt import Offset, Token

from django_upgrade.ast import ast_start_offset
from django_upgrade.data import Fixer, State, TokenFunc
from django_upgrade.tokens import OP, find_last_token, reverse_find

fixer = Fixer(
    __name__,
    min_version=(5, 0),
    condition=lambda state: state.looks_like_models_file,
)

# Cache defined enumeration types by module
module_defined_enumeration_types: WeakKeyDictionary[ast.Module, dict[str, int]] = (
    WeakKeyDictionary()
)


def defined_enumeration_types(module: ast.Module, up_to_line: int) -> set[str]:
    """
    Return a set of enumeration type class names defined in the given module, up to a line number.
    """
    if module not in module_defined_enumeration_types:
        enum_dict = {}
        from_imports: defaultdict[str, set[str]] = defaultdict(set)
        for node in module.body:
            if (
                isinstance(node, ast.ImportFrom)
                and node.level == 0
                and node.module is not None
            ):
                from_imports[node.module].update(
                    name.name
                    for name in node.names
                    if name.asname is None and name.name != "*"
                )
            elif isinstance(node, ast.ClassDef):
                # Check if the class inherits from one of Django's choice types
                for base in node.bases:
                    if _is_django_choices_type(from_imports, base):
                        enum_dict[node.name] = node.lineno
                        break
        module_defined_enumeration_types[module] = enum_dict

    return {
        name
        for name, line in module_defined_enumeration_types[module].items()
        if line <= up_to_line
    }


DJANGO_CHOICES_TYPES = {
    "TextChoices",
    "IntegerChoices",
    "Choices",
}


def _is_django_choices_type(
    from_imports: defaultdict[str, set[str]], node: ast.expr
) -> bool:
    """Check if an AST node refers to a Django enumeration type base class."""
    return (
        isinstance(node, ast.Name)
        and node.id in DJANGO_CHOICES_TYPES
        and (
            node.id in from_imports["django.db.models"]
            or node.id in from_imports["django.db.models.enums"]
        )
    ) or (
        isinstance(node, ast.Attribute)
        and node.attr in DJANGO_CHOICES_TYPES
        and isinstance(node.value, ast.Name)
        and (
            (node.value.id == "models" and node.value.id in from_imports["django.db"])
            or (
                node.value.id == "enums"
                and node.value.id in from_imports["django.db.models"]
            )
        )
    )


@fixer.register(ast.Call)
def visit_Call(
    state: State,
    node: ast.Call,
    parents: tuple[ast.AST, ...],
) -> Iterable[tuple[Offset, TokenFunc]]:
    if (
        (
            isinstance(node.func, ast.Attribute)
            and isinstance(node.func.value, ast.Name)
            and node.func.attr.endswith("Field")
        )
        or (isinstance(node.func, ast.Name) and node.func.id.endswith("Field"))
    ) and any(
        kw.arg == "choices"
        and isinstance(kw.value, ast.Attribute)
        and (target_node := kw.value).attr == "choices"
        and isinstance(target_node.value, ast.Name)
        and (
            target_node.value.id
            in defined_enumeration_types(
                cast(ast.Module, parents[0]),
                node.lineno,
            )
        )
        for kw in node.keywords
    ):
        yield ast_start_offset(target_node), partial(remove_choices, node=target_node)


def remove_choices(tokens: list[Token], i: int, node: ast.Attribute) -> None:
    j = find_last_token(tokens, i, node=node)
    i = reverse_find(tokens, j, name=OP, src=".")
    del tokens[i : j + 1]

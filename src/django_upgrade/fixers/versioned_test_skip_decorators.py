"""
Drop test skip decorators for old Django versions like:

import unittest

import django
import pytest
from django.test import TestCase

class ExampleTests(TestCase):
    @unittest.skipIf(django.VERSION < (5, 1), "Django 5.1+")
    def test_one(self):
        ...

    @unittest.skipUnless(django.VERSION >= (5, 1), "Django 5.1+")
    def test_two(self):
        ...

    @pytest.mark.skipif(django.VERSION < (5, 1), reason="Django 5.1+")
    def test_three(self):
        ...
"""

from __future__ import annotations

import ast
from collections.abc import Iterable
from functools import partial

from tokenize_rt import Offset

from django_upgrade.ast import ast_start_offset
from django_upgrade.ast import is_passing_comparison
from django_upgrade.data import Fixer
from django_upgrade.data import State
from django_upgrade.data import TokenFunc
from django_upgrade.tokens import erase_decorator

fixer = Fixer(
    __name__,
    min_version=(0, 0),
)


@fixer.register(ast.FunctionDef)
def visit_FunctionDef(
    state: State,
    node: ast.FunctionDef,
    parents: tuple[ast.AST, ...],
) -> Iterable[tuple[Offset, TokenFunc]]:
    yield from _handle_decorator(state, node, parents)


@fixer.register(ast.ClassDef)
def visit_ClassDef(
    state: State,
    node: ast.ClassDef,
    parents: tuple[ast.AST, ...],
) -> Iterable[tuple[Offset, TokenFunc]]:
    yield from _handle_decorator(state, node, parents)


def _handle_decorator(
    state: State,
    node: ast.FunctionDef | ast.ClassDef,
    parents: tuple[ast.AST, ...],
) -> Iterable[tuple[Offset, TokenFunc]]:
    for decorator in node.decorator_list:
        if (
            isinstance(decorator, ast.Call)
            and (
                (
                    isinstance(decorator.func, ast.Attribute)
                    and isinstance(decorator.func.value, ast.Name)
                    and decorator.func.value.id == "unittest"
                    and decorator.func.attr in ("skipIf", "skipUnless")
                    and (ident := ("unittest", decorator.func.attr))
                )
                or (
                    isinstance(decorator.func, ast.Name)
                    and (decorator.func.id in ("skipIf", "skipUnless"))
                    and decorator.func.id in state.from_imports["unittest"]
                    and (ident := ("unittest", decorator.func.id))
                )
                # or pytest.mark.skipif
                or (
                    isinstance(decorator.func, ast.Attribute)
                    and isinstance(decorator.func.value, ast.Attribute)
                    and isinstance(decorator.func.value.value, ast.Name)
                    and decorator.func.value.value.id == "pytest"
                    and decorator.func.value.attr == "mark"
                    and decorator.func.attr == "skipif"
                    and (ident := ("pytest", "mark.skipif"))
                )
            )
            and (
                (
                    ident[0] == "unittest"
                    and len(decorator.args) == 2
                    and len(decorator.keywords) == 0
                )
                or (
                    ident[0] == "pytest"
                    and len(decorator.args) == 1
                    and len(decorator.keywords) == 1
                    and decorator.keywords[0].arg == "reason"
                )
            )
            and isinstance(decorator.args[0], ast.Compare)
            and (
                (pass_fail := is_passing_comparison(decorator.args[0], state))
                is not None
            )
            and (
                (ident == ("unittest", "skipIf") and pass_fail == "fail")
                or (ident == ("unittest", "skipUnless") and pass_fail == "pass")
                or (ident == ("pytest", "mark.skipif") and pass_fail == "fail")
            )
        ):
            yield ast_start_offset(decorator), partial(erase_decorator, node=decorator)

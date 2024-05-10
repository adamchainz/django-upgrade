from __future__ import annotations

import ast
from textwrap import dedent

from django_upgrade.data import Settings
from django_upgrade.main import apply_fixers


def check_noop(contents: str, settings: Settings, filename: str = "example.py") -> None:
    dedented_contents = dedent(contents)
    fixed = apply_fixers(dedented_contents, settings=settings, filename=filename)
    assert fixed == dedented_contents


def check_transformed(
    before: str, after: str, settings: Settings, filename: str = "example.py"
) -> None:
    dedented_before = dedent(before)
    dedented_after = dedent(after)
    ast.parse(dedented_after)  # check that the target is valid python code
    fixed = apply_fixers(dedented_before, settings=settings, filename=filename)
    assert fixed == dedented_after

from __future__ import annotations

import ast

import pytest

from django_upgrade.ast import get_module_names


class TestGetModuleNames:
    def names(self, src: str) -> frozenset[str]:
        return get_module_names(ast.parse(src))

    @pytest.mark.parametrize(
        "src",
        (
            "x",
            "x = 1",
            "del x",
        ),
    )
    def test_name(self, src: str) -> None:
        assert self.names(src) == frozenset({"x"})

    @pytest.mark.parametrize(
        "src",
        (
            "import x",
            "import y as x",
            "from m import x",
            "from m import y as x",
        ),
    )
    def test_import_alias(self, src: str) -> None:
        assert self.names(src) == frozenset({"x"})

    def test_dotted_import(self) -> None:
        assert self.names("import x.y") == frozenset({"x"})

    def test_function_def(self) -> None:
        assert self.names("def x(): pass") == frozenset({"x"})

    def test_async_function_def(self) -> None:
        assert self.names("async def x(): pass") == frozenset({"x"})

    def test_class_def(self) -> None:
        assert self.names("class x: pass") == frozenset({"x"})

    def test_arg(self) -> None:
        assert self.names("def f(x): pass") == frozenset({"f", "x"})

    def test_assignment(self) -> None:
        assert self.names("y = 1") == frozenset({"y"})

    @pytest.mark.parametrize(
        ("src", "expected"),
        (
            ("match value:\n    case x:\n        pass", frozenset({"value", "x"})),
            ("match value:\n    case [*x]:\n        pass", frozenset({"value", "x"})),
            ("match value:\n    case {**x}:\n        pass", frozenset({"value", "x"})),
        ),
    )
    def test_pattern(self, src: str, expected: frozenset[str]) -> None:
        assert self.names(src) == expected

    def test_except_handler(self) -> None:
        assert self.names(
            "try:\n    pass\nexcept Exception as x:\n    pass"
        ) == frozenset({"Exception", "x"})

    def test_caching(self) -> None:
        module = ast.parse("x = 1")
        assert get_module_names(module) is get_module_names(module)

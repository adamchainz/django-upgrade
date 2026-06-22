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
    def test_alias(self, src: str) -> None:
        assert self.names(src) == frozenset({"x"})

    def test_function_def(self) -> None:
        assert self.names("def x(): pass") == frozenset({"x"})

    def test_async_function_def(self) -> None:
        assert self.names("async def x(): pass") == frozenset({"x"})

    def test_class_def(self) -> None:
        assert self.names("class x: pass") == frozenset({"x"})

    def test_arg(self) -> None:
        assert self.names("def f(x): pass") == frozenset({"f", "x"})

    def test_not_present(self) -> None:
        assert self.names("y = 1") == frozenset({"y"})

    def test_caching(self) -> None:
        module = ast.parse("x = 1")
        assert get_module_names(module) is get_module_names(module)

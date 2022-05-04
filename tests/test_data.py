from __future__ import annotations

import pytest

from django_upgrade.data import Settings, State


@pytest.mark.parametrize(
    ("filename"),
    (
        "test_example.py",
        "example_test.py",
        "test.py",
        "tests.py",
        "myapp/test.py",
        "myapp/tests.py",
        "myapp/tests/base.py",
        "myapp/tests/__init__.py",
        "myapp/test_example.py",
        "myapp/tests_example.py",
        "myapp/example_test.py",
        "myapp/example_tests.py",
    ),
)
def test_looks_like_test_file_true(filename):
    state = State(
        settings=Settings(target_version=(4, 0)),
        filename=filename,
        from_imports={},
    )
    assert state.looks_like_test_file()


@pytest.mark.parametrize(
    ("filename"),
    (
        "conftest.py",
        "protester.py",
        "myapp/protests/models.py",
    ),
)
def test_looks_like_test_file_false(filename):
    state = State(
        settings=Settings(target_version=(4, 0)),
        filename=filename,
        from_imports={},
    )
    assert not state.looks_like_test_file()


@pytest.mark.parametrize(
    ("filename"),
    (
        "__init__.py",
        "package/__init__.py",
        r"package\__init__.py",
        "project/package/__init__.py",
        r"project\package\__init__.py",
    ),
)
def test_looks_like_dunder_init_file_true(filename):
    state = State(
        settings=Settings(target_version=(4, 0)),
        filename=filename,
        from_imports={},
    )
    assert state.looks_like_test_file()


@pytest.mark.parametrize(
    ("filename"),
    (
        "__thing__init__.py",
        "thing-__init__.py",
        "__init___py",
        "_init_.py",
        "__init.py",
        "init__.py",
    ),
)
def test_looks_like_dunder_init_file_false(filename):
    state = State(
        settings=Settings(target_version=(4, 0)),
        filename=filename,
        from_imports={},
    )
    assert not state.looks_like_test_file()

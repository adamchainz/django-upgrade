from __future__ import annotations

import re
from collections import defaultdict
from pathlib import Path

import pytest

from django_upgrade.data import FIXERS
from django_upgrade.data import Settings
from django_upgrade.data import State

settings = Settings(target_version=(4, 0))


def make_state(filename: str) -> State:
    return State(
        settings=settings,
        filename=filename,
        from_imports=defaultdict(set),
    )


@pytest.mark.parametrize(
    "filename",
    (
        "admin.py",
        "myapp/admin.py",
        "myapp\\admin.py",
        "myapp/admin/file.py",
        "myapp\\admin\\file.py",
        "myapp/blog/admin/article.py",
        "myapp\\blog\\admin\\article.py",
        "myapp/custom_admin.py",
        "myapp\\custom_admin.py",
        "myapp/custom_admin/file.py",
        "myapp\\custom_admin\\file.py",
        "myapp/admin_custom.py",
        "myapp\\admin_custom.py",
        "myapp/admin_custom/file.py",
        "myapp\\admin_custom\\file.py",
    ),
)
def test_looks_like_admin_file_true(filename: str) -> None:
    assert make_state(filename).looks_like_admin_file


@pytest.mark.parametrize(
    "filename",
    (
        "administrator.py",
        "blog/adm/article.py",
        "blog\\adm\\article.py",
    ),
)
def test_looks_like_admin_file_false(filename: str) -> None:
    assert not make_state(filename).looks_like_admin_file


@pytest.mark.parametrize(
    "filename",
    (
        "management/commands/test.py",
        "management\\commands\\test.py",
        "myapp/management/commands/test.py",
        "myapp\\management\\commands\\test.py",
        "myapp/subapp/management/commands/test.py",
        "myapp\\subapp\\management\\commands\\test.py",
        "myapp/subapp/management/commands/test/subcommand.py",
        "myapp\\subapp\\management\\commands\\test\\subcommand.py",
    ),
)
def test_looks_like_command_file_true(filename: str) -> None:
    assert make_state(filename).looks_like_command_file


@pytest.mark.parametrize(
    "filename",
    (
        "test.py",
        "management/commands.py",
        "management\\commands.py",
        "myapp/management/commands.py",
        "myapp\\management\\commands.py",
        "myapp/mgmt/commands.py",
        "myapp\\mgmt\\commands.py",
        "myapp/management/something/commands/example.py",
        "myapp\\management\\something\\commands\\example.py",
        "myapp/commands/management/example.py",
        "myapp\\commands\\management\\example.py",
    ),
)
def test_looks_like_command_file_false(filename: str) -> None:
    assert not make_state(filename).looks_like_command_file


@pytest.mark.parametrize(
    "filename",
    (
        "__init__.py",
        "package/__init__.py",
        "package\\__init__.py",
        "project/package/__init__.py",
        "project\\package\\__init__.py",
    ),
)
def test_looks_like_dunder_init_file_true(filename: str) -> None:
    assert make_state(filename).looks_like_dunder_init_file


@pytest.mark.parametrize(
    "filename",
    (
        "__thing__init__.py",
        "thing-__init__.py",
        "__init___py",
        "_init_.py",
        "__init.py",
        "init__.py",
    ),
)
def test_looks_like_dunder_init_file_false(filename: str) -> None:
    assert not make_state(filename).looks_like_dunder_init_file


@pytest.mark.parametrize(
    "filename",
    (
        "project/migrations/0238_auto_20200424_1249.py",
        "project\\migrations\\0238_auto_20200424_1249.py",
        "another_project/migrations/0001_initial.py",
        "another_project\\migrations\\0001_initial.py",
    ),
)
def test_looks_like_migrations_file_true(filename: str) -> None:
    assert make_state(filename).looks_like_migrations_file


@pytest.mark.parametrize(
    "filename",
    (
        "0238_auto_20200424_1249.py",
        "package/0001_initial.py",
        "package\\0001_initial.py",
        "migration/0001_initial.py",
        "migration\\0001_initial.py",
    ),
)
def test_looks_like_migrations_file_false(filename: str) -> None:
    assert not make_state(filename).looks_like_migrations_file


@pytest.mark.parametrize(
    "filename",
    (
        "my_app/models/blog.py",
        "my_app\\models\\blog.py",
        "my_app/models/blogging/blog.py",
        "my_app\\models\\blogging\\blog.py",
        "my_other_app/models.py",
        "my_other_app\\models.py",
        "my_app/models/__init__.py",
    ),
)
def test_looks_like_models_file_true(filename: str) -> None:
    assert make_state(filename).looks_like_models_file


@pytest.mark.parametrize(
    "filename",
    (
        "my_app/model.py",
        "my_app/model/blog.py",
        "my_app/model\\blog.py",
        "my_app/test_models/test_foo.py",
        "my_app/tests/test_models.py",
        "my_app/migrations/0020_delete_old_models.py",
    ),
)
def test_looks_like_models_file_false(filename: str) -> None:
    assert not make_state(filename).looks_like_models_file


@pytest.mark.parametrize(
    "filename",
    (
        "settings.py",
        "myapp/settings.py",
        "myapp\\settings.py",
        "myapp/settings/prod.py",
        "myapp\\settings\\prod.py",
        "myapp/prod_settings.py",
        "myapp\\prod_settings.py",
        "myapp/local_settings.py",
        "myapp\\local_settings.py",
        "myapp/settings_tests.py",
        "myapp\\settings_tests.py",
    ),
)
def test_looks_like_settings_file_true(filename: str) -> None:
    assert make_state(filename).looks_like_settings_file


@pytest.mark.parametrize(
    "filename",
    (
        "upsettings.py",
        "settingsprod.py",
    ),
)
def test_looks_like_settings_file_false(filename: str) -> None:
    assert not make_state(filename).looks_like_settings_file


@pytest.mark.parametrize(
    "filename",
    (
        "test_example.py",
        "example_test.py",
        "test.py",
        "tests.py",
        "myapp/test.py",
        "myapp\\test.py",
        "myapp/tests.py",
        "myapp\\tests.py",
        "myapp/tests/base.py",
        "myapp\\tests\\base.py",
        "myapp/tests/__init__.py",
        "myapp\\tests\\__init__.py",
        "myapp/test_example.py",
        "myapp\\test_example.py",
        "myapp/tests_example.py",
        "myapp\\tests_example.py",
        "myapp/example_test.py",
        "myapp\\example_test.py",
        "myapp/example_tests.py",
        "myapp\\example_tests.py",
    ),
)
def test_looks_like_test_file_true(filename: str) -> None:
    assert make_state(filename).looks_like_test_file


@pytest.mark.parametrize(
    "filename",
    (
        "conftest.py",
        "protester.py",
        "myapp/protests/models.py",
        "myapp\\protests\\models.py",
    ),
)
def test_looks_like_test_file_false(filename: str) -> None:
    assert not make_state(filename).looks_like_test_file


def test_all_fixers_are_documented() -> None:
    readme = (Path(__name__).parent.parent / "README.rst").read_text()
    docs = set()
    for line in readme.splitlines():
        match = re.match(r"\*\*Name:\*\* ``(.+)``", line)
        if not match:
            continue
        docs.add(match[1])

    fixers = {fixer.name for fixer in FIXERS}

    invalid = docs - fixers
    assert not invalid

    undocumented = fixers - docs
    assert not undocumented

from textwrap import dedent

from django_upgrade._data import Settings
from django_upgrade._main import _fix_plugins

settings = Settings(target_version=(3, 0))


def check_noop(contents: str, settings: Settings) -> None:
    dedented_contents = dedent(contents)
    fixed = _fix_plugins(dedented_contents, settings=settings)
    assert fixed == dedented_contents


def check_transformed(before: str, after: str, settings: Settings) -> None:
    dedented_before = dedent(before)
    dedented_after = dedent(after)
    fixed = _fix_plugins(dedented_before, settings=settings)
    assert fixed == dedented_after

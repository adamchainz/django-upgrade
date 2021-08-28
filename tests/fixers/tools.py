from textwrap import dedent

from django_upgrade.data import Settings
from django_upgrade.main import apply_fixers

settings = Settings(target_version=(3, 0))


def check_noop(contents: str, settings: Settings, filename: str = "example.py") -> None:
    dedented_contents = dedent(contents)
    fixed = apply_fixers(dedented_contents, settings=settings, filename=filename)
    assert fixed == dedented_contents


def check_transformed(
    before: str, after: str, settings: Settings, filename: str = "example.py"
) -> None:
    dedented_before = dedent(before)
    dedented_after = dedent(after)
    fixed = apply_fixers(dedented_before, settings=settings, filename=filename)
    assert fixed == dedented_after

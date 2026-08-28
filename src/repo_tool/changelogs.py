"""Shared logic for reading and updating changelog files.

Changelogs are expected to follow the reStructuredText structure:

.. code-block:: rst

    =========
    Changelog
    =========

    Unreleased
    ----------

    * An entry.

    1.2.3 (2024-01-01)
    ------------------

    * Another entry.
"""

from __future__ import annotations

import datetime as dt
import re
from pathlib import Path

SEARCH_PATHS = (
    "docs/changelog.rst",
    "CHANGELOG.rst",
)

TITLE_RE = re.compile(r"=========\nChangelog\n=========\n\n")
UNRELEASED_RE = re.compile(r"(Unreleased|Pending)\n-+\n\n")
HEADING_RE = re.compile(r"^\S.*\n-+\n", re.MULTILINE)


class ChangelogError(Exception):
    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(message)


class ChangelogNotFound(ChangelogError):
    def __init__(self) -> None:
        super().__init__(
            "No changelog file found (searched: " + ", ".join(SEARCH_PATHS) + ")."
        )


class ChangelogParseError(ChangelogError):
    pass


def find(root: Path | None = None) -> Path:
    if root is None:
        root = Path()
    for name in SEARCH_PATHS:
        path = root / name
        if path.exists():
            return path
    raise ChangelogNotFound


def add_entry(content: str, text: str) -> str:
    """
    Add an entry at the end of the unreleased section, creating the section
    if it does not exist.
    """
    entry = text.rstrip("\n")
    if not entry.startswith("* "):
        entry = f"* {entry}"

    title_match = TITLE_RE.search(content)
    if title_match is None:
        raise ChangelogParseError("Changelog title not found.")
    pos = title_match.end()

    unreleased_match = UNRELEASED_RE.match(content, pos)
    if unreleased_match is None:
        new_section = f"Unreleased\n----------\n\n{entry}\n\n"
        return content[:pos] + new_section + content[pos:]

    section_start = unreleased_match.end()
    next_heading = HEADING_RE.search(content, section_start)
    if next_heading is None:
        return content.rstrip("\n") + f"\n{entry}\n"

    before = content[: next_heading.start()].rstrip("\n")
    return before + f"\n{entry}\n\n" + content[next_heading.start() :]


def start_version(content: str, version: str, date: dt.date) -> str:
    """
    Replace the unreleased section heading, if any, with a heading for the
    given version, released today.
    """
    lines = content.splitlines()
    if lines[:4] != ["=========", "Changelog", "=========", ""]:
        raise ChangelogParseError("Changelog title not found.")
    if lines[4] in ("Unreleased", "Pending"):
        if lines[5] != "-" * len(lines[4]) or lines[6] != "":
            raise ChangelogParseError(
                f"Malformed {lines[4]!r} section heading.",
            )
        del lines[4:7]

    if not lines[4].startswith("* "):
        raise ChangelogParseError("No unreleased changelog entries found.")

    version_line = f"{version} ({date.isoformat()})"
    lines[4:4] = [version_line, "-" * len(version_line), ""]
    return "\n".join(lines) + "\n"

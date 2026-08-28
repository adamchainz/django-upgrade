from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence
from importlib import metadata
from typing import cast

from repo_tool.commands import changelog, release, upgrade_dependencies


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="repo-tool",
        description="Multitool for maintaining many repositories.",
    )
    if sys.version_info >= (3, 14):
        parser.suggest_on_error = True
    parser.add_argument(
        "--version",
        action="version",
        version=metadata.version("repo-tool"),
        help="Show the version number and exit.",
    )
    subparsers = parser.add_subparsers(
        title="commands",
        metavar="command",
        required=True,
    )
    # New commands: add a module in repo_tool.commands defining add_arguments()
    # and call it here.
    changelog.add_arguments(subparsers)
    release.add_arguments(subparsers)
    upgrade_dependencies.add_arguments(subparsers)

    args = parser.parse_args(argv)
    return cast(int, args.func(args))

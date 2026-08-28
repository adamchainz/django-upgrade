from __future__ import annotations

import argparse
import sys

from repo_tool import changelogs


def add_arguments(
    subparsers: argparse._SubParsersAction[argparse.ArgumentParser],
) -> None:
    parser = subparsers.add_parser(
        "changelog",
        help="Work with the repository's changelog file.",
    )
    subsubparsers = parser.add_subparsers(
        title="subcommands",
        metavar="subcommand",
        required=True,
    )

    append_parser = subsubparsers.add_parser(
        "append",
        help=(
            "Add an entry to the unreleased section of the changelog, "
            "creating the section if necessary."
        ),
    )
    append_parser.add_argument(
        "entry",
        help="Text of the entry, e.g. 'Support Python 3.15.'.",
    )
    append_parser.set_defaults(func=append_run)


def append_run(args: argparse.Namespace) -> int:
    try:
        path = changelogs.find()
        content = path.read_text()
        updated = changelogs.add_entry(content, args.entry)
    except changelogs.ChangelogError as exc:
        print(f"❌ {exc.message}", file=sys.stderr)
        return 1
    path.write_text(updated)
    print(f"✅ Added entry to {path}")
    return 0

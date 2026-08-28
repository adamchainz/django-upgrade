from __future__ import annotations

import argparse
import re
import sys
import time
import urllib.request
from pathlib import Path

from repo_tool import gitutils
from repo_tool.gitutils import run


def add_arguments(
    subparsers: argparse._SubParsersAction[argparse.ArgumentParser],
) -> None:
    parser = subparsers.add_parser(
        "upgrade-dependencies",
        help=(
            "Upgrade the current repository's pinned dependencies and push "
            "the changes as an auto-merging PR."
        ),
    )
    parser.set_defaults(func=run_command)


BRANCH_NAME = "upgrade_dependencies"


def run_command(args: argparse.Namespace) -> int:
    if gitutils.uncommitted_changes():
        print("❌ Uncommitted changes.", file=sys.stderr)
        return 1

    run(["git", "switch", gitutils.default_branch()])
    run(["git", "pull"])

    if gitutils.branch_exists(BRANCH_NAME):
        print(f"Branch {BRANCH_NAME} already exists.")
        return 0

    # Upgrade Python dependencies
    if Path("uv.lock").exists():
        run(["uv", "lock", "--upgrade"])

    # Upgrade pinned Rust version
    if Path("rust-toolchain.toml").exists():
        upgrade_rust_toolchain()

    # Upgrade Rust dependencies
    if Path("Cargo.lock").exists():
        run(["cargo", "update"])

    if not gitutils.uncommitted_changes():
        print("No changes.")
        return 0

    run(["git", "switch", "-c", BRANCH_NAME])
    run(["git", "commit", "--all", "--message", "Upgrade dependencies"])
    run(["git", "push", "--set-upstream", "origin", BRANCH_NAME])
    run(["gh", "pr", "create", "--fill"])
    time.sleep(1)
    run(["gh", "pr", "merge", "--squash", "--delete-branch", "--auto", BRANCH_NAME])
    # Avoid hitting GitHub rate limit of ~10 PRs per minute when running
    # across many repositories.
    time.sleep(19)
    return 0


RUST_VERSION_URL = "https://raw.githubusercontent.com/rust-lang/rust/stable/src/version"


def upgrade_rust_toolchain() -> None:
    latest_version = fetch_latest_rust_version()
    # Drop the patch component: "1.89.0" -> "1.89"
    minor_version = latest_version.rsplit(".", 1)[0]

    toolchain_path = Path("rust-toolchain.toml")
    content = toolchain_path.read_text()
    updated = re.sub(
        r'^channel = "[0-9.]+"',
        f'channel = "{minor_version}"',
        content,
        flags=re.MULTILINE,
    )
    if updated != content:
        toolchain_path.write_text(updated)

    # Match MSRV to the toolchain, only for packages not published to crates.io
    cargo_path = Path("Cargo.toml")
    if cargo_path.exists():
        cargo_content = cargo_path.read_text()
        if re.search(r"^publish = false$", cargo_content, flags=re.MULTILINE):
            cargo_updated = re.sub(
                r'^rust-version = "[0-9.]+"',
                f'rust-version = "{minor_version}"',
                cargo_content,
                flags=re.MULTILINE,
            )
            if cargo_updated != cargo_content:
                cargo_path.write_text(cargo_updated)


def fetch_latest_rust_version() -> str:
    with urllib.request.urlopen(RUST_VERSION_URL) as response:
        return response.read().decode().strip()  # type: ignore [no-any-return]

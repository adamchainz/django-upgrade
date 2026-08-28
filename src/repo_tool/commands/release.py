from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import re
import sys
import tomllib
from glob import glob
from pathlib import Path
from textwrap import dedent

from packaging.version import Version

from repo_tool import changelogs, gitutils
from repo_tool.gitutils import run


def add_arguments(
    subparsers: argparse._SubParsersAction[argparse.ArgumentParser],
) -> None:
    parser = subparsers.add_parser(
        "release",
        help="Perform a release for the current Python or Rust package.",
    )
    parser.add_argument("change", choices=["major", "minor", "patch"])
    parser.add_argument("--sdist-only", action="store_true")
    parser.add_argument("--skip-changelog", action="store_true")
    parser.set_defaults(func=run_command)


def run_command(args: argparse.Namespace) -> int:
    change = args.change
    sdist_only = args.sdist_only
    skip_changelog = args.skip_changelog

    if gitutils.uncommitted_changes():
        print("❌ Uncommitted changes.", file=sys.stderr)
        return 1

    default_branch = gitutils.default_branch()
    run(["git", "switch", default_branch])
    run(["git", "pull"])

    # check that we are in the root of the repository
    proc = run(
        ["git", "rev-parse", "--path-format=relative", "--show-toplevel"],
        capture_output=True,
        text=True,
    )
    if proc.stdout.strip() != "./":
        print("❌ Not in the root of the repository", file=sys.stderr)
        return 1

    # check for unpushed commits
    proc = run(
        ["git", "rev-list", "HEAD...@{u}", "--count"], capture_output=True, text=True
    )
    if proc.stdout.strip() != "0":
        print("❌ Unpushed commits", file=sys.stderr)
        return 1

    proc = run(["git", "tag", "--contains", "HEAD"], capture_output=True, text=True)
    tag = proc.stdout.strip()
    if tag != "":
        print(
            f"❌ Current commit already tagged {tag!r}",
            file=sys.stderr,
        )
        return 1

    if Path("pyproject.toml").exists():
        with Path("pyproject.toml").open("rb") as fp:
            pyproject_data = tomllib.load(fp)
        current_version = Version(pyproject_data["project"]["version"])
        name = pyproject_data["project"]["name"]

    elif Path("Cargo.toml").exists():
        with Path("Cargo.toml").open("rb") as fp:
            cargo_data = tomllib.load(fp)
        current_version = Version(cargo_data["package"]["version"])
        name = cargo_data["package"]["name"]

    else:
        print("❌ No pyproject.toml or Cargo.toml found", file=sys.stderr)
        return 1

    version = bump_version(current_version, change)

    if not check_ci_passing(name):
        return 1

    if Path("pyproject.toml").exists():
        replace_version_line(Path("pyproject.toml"), version)
    if Path("uv.lock").exists():
        run(["uv", "lock"])
    if Path("Cargo.toml").exists():
        replace_version_line(Path("Cargo.toml"), version)
        run(["cargo", "check"])

    if not skip_changelog:
        try:
            changelog_path = changelogs.find()
            changelog_contents = changelog_path.read_text()
            updated = changelogs.start_version(
                changelog_contents, version, dt.date.today()
            )
        except changelogs.ChangelogError as exc:
            print(f"❌ {exc.message}", file=sys.stderr)
            return 1
        changelog_path.write_text(updated)

    files_to_add = []
    if Path("pyproject.toml").exists():
        files_to_add.append("pyproject.toml")
    if Path("Cargo.toml").exists():
        files_to_add.extend(["Cargo.toml", "Cargo.lock"])
    if Path("uv.lock").exists():
        files_to_add.append("uv.lock")
    if not skip_changelog:
        files_to_add.append(str(changelog_path))
    run(["git", "commit", "--message", f"Version {version}", "--", *files_to_add])

    workflow_path = Path(".github/workflows/main.yml")
    if not workflow_path.exists() or "release:" not in workflow_path.read_text():
        # Local build
        assert Path("pyproject.toml").exists()

        run(["rm", "-rf", "build", "dist", *glob("src/*.egg-info")])

        build_command = [
            "uvx",
            "--from",
            "build",
            "pyproject-build",
            "--installer",
            "uv",
        ]
        if sdist_only:
            build_command.append("--sdist")
        run(build_command, env={**os.environ, "PIP_REQUIRE_VIRTUALENV": "0"})

        run(["uvx", "twine", "check", *glob("dist/*")])
        run(["uvx", "twine", "upload", *glob("dist/*")])

    run(["git", "push", "origin", default_branch])
    run(["git", "tag", "--annotate", version, "--message", f"Version {version}"])
    run(["git", "push", "--tags", "origin", version])
    return 0


def bump_version(current_version: Version, change: str) -> str:
    if change == "major":
        return f"{current_version.major + 1}.0.0"
    elif change == "minor":
        return f"{current_version.major}.{current_version.minor + 1}.0"
    else:
        assert change == "patch"
        return (
            f"{current_version.major}.{current_version.minor}"
            + f".{current_version.micro + 1}"
        )


def replace_version_line(path: Path, version: str) -> None:
    content = path.read_text()
    updated = re.sub(
        r'^version = ".*"$',
        f'version = "{version}"',
        content,
        count=1,
        flags=re.MULTILINE,
    )
    path.write_text(updated)


STATUS_QUERY = dedent(
    """\
    query ($owner: String!, $name: String!, $commit: String!) {
      repository(owner: $owner, name: $name) {
        object(expression: $commit) {
          ... on Commit {
            checkSuites(first: 100) {
              nodes {
                creator {
                  name
                }
                resourcePath
                status
                app {
                  name
                }
                conclusion
                checkRuns(first: 10) {
                  nodes {
                    conclusion
                    name
                  }
                }
              }
            }
          }
        }
      }
    }
    """
)


def check_ci_passing(name: str) -> bool:
    """
    Check GitHub Actions are all successful for the current commit.

    May be replaceable in future with gh cli builtin:
    https://github.com/cli/cli/issues/1055
    """
    latest_commit = run(
        ["git", "rev-parse", "HEAD"], capture_output=True, text=True
    ).stdout.strip()
    checks_data = json.loads(
        run(
            [
                "gh",
                "api",
                "graphql",
                "-F",
                r"owner={owner}",
                "-F",
                r"name={repo}",
                "-F",
                f"commit={latest_commit}",
                "-f",
                f"query={STATUS_QUERY}",
            ],
            capture_output=True,
            text=True,
        ).stdout
    )
    check_suites = checks_data["data"]["repository"]["object"]["checkSuites"]["nodes"]
    if not check_suites:
        print(
            "❌ No check suites found for the latest commit - tests may not have started yet.",
            file=sys.stderr,
        )
        return False
    check_suites = [
        s
        for s in check_suites
        if not (
            # Ignored apps from pytest-dev org, which appear due to the organization
            # configuration, but I don't use them.
            name == "pytest-randomly"
            and s["app"] is not None
            and s["app"]["name"]
            in (
                "AppVeyor",
                "Claude",
                "Read the Docs Community",
                "Travis CI",
            )
        )
        and not (
            # Dependabot allowed to fail, sometimes it's broken, and all it
            # does is make PRs
            s["app"] is not None
            and s["app"]["name"] == "GitHub Actions"
            and len(s["checkRuns"]["nodes"]) == 1
            and s["checkRuns"]["nodes"][0]["name"] == "Dependabot"
        )
        and not (
            # Claude just does review
            s["app"] is not None and s["app"]["name"] == "Claude"
        )
    ]
    if not all(s["conclusion"] == "SUCCESS" for s in check_suites):
        print("❌ Not all checks are successful:", file=sys.stderr)
        for check_suite in check_suites:
            print(
                f"    {check_suite['app']['name']} - {check_suite['status']} / {check_suite['conclusion']}",
                file=sys.stderr,
            )
            nodes = check_suite["checkRuns"]["nodes"]
            if nodes:
                for check_run in nodes:
                    print(
                        f"        {check_run['name']}: {check_run['conclusion']}",
                        file=sys.stderr,
                    )
            else:
                print(
                    "        (No specific runs.)",
                    file=sys.stderr,
                )
        return False
    return True

from __future__ import annotations

import datetime as dt
import json
from collections.abc import Callable
from types import SimpleNamespace
from typing import Any

import pytest
from packaging.version import Version

from repo_tool import gitutils
from repo_tool.commands import release
from repo_tool.main import main

TITLE = "=========\nChangelog\n=========\n\n"


def make_fake_run(
    commands: list[list[str]],
    *,
    toplevel: str = "./\n",
    unpushed: str = "0\n",
    contained_tags: str = "\n",
) -> Callable[..., SimpleNamespace]:
    def fake_run(command: list[str], **kwargs: Any) -> SimpleNamespace:
        commands.append(command)
        stdout = ""
        if command[:2] == ["git", "rev-parse"] and "--show-toplevel" in command:
            stdout = toplevel
        elif command[:2] == ["git", "rev-list"]:
            stdout = unpushed
        elif command[:3] == ["git", "tag", "--contains"]:
            stdout = contained_tags
        return SimpleNamespace(stdout=stdout)

    return fake_run


class TestRunCommand:
    @pytest.fixture(autouse=True)
    def in_tmp_path(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        monkeypatch.setattr(gitutils, "uncommitted_changes", lambda: False)
        monkeypatch.setattr(gitutils, "default_branch", lambda: "main")
        return tmp_path

    def test_no_change(self):
        with pytest.raises(SystemExit) as excinfo:
            main(["release"])

        assert excinfo.value.code == 2

    def test_invalid_change(self):
        with pytest.raises(SystemExit) as excinfo:
            main(["release", "mega"])

        assert excinfo.value.code == 2

    def test_uncommitted_changes(self, monkeypatch, capsys):
        monkeypatch.setattr(gitutils, "uncommitted_changes", lambda: True)

        result = main(["release", "minor"])

        assert result == 1
        out, err = capsys.readouterr()
        assert err == "❌ Uncommitted changes.\n"

    def test_not_repo_root(self, monkeypatch, capsys):
        commands: list[list[str]] = []
        monkeypatch.setattr(release, "run", make_fake_run(commands, toplevel="../\n"))

        result = main(["release", "minor"])

        assert result == 1
        out, err = capsys.readouterr()
        assert err == "❌ Not in the root of the repository\n"

    def test_unpushed_commits(self, monkeypatch, capsys):
        commands: list[list[str]] = []
        monkeypatch.setattr(release, "run", make_fake_run(commands, unpushed="2\n"))

        result = main(["release", "minor"])

        assert result == 1
        out, err = capsys.readouterr()
        assert err == "❌ Unpushed commits\n"

    def test_already_tagged(self, monkeypatch, capsys):
        commands: list[list[str]] = []
        monkeypatch.setattr(
            release, "run", make_fake_run(commands, contained_tags="1.2.3\n")
        )

        result = main(["release", "minor"])

        assert result == 1
        out, err = capsys.readouterr()
        assert err == "❌ Current commit already tagged '1.2.3'\n"

    def test_no_package_metadata(self, monkeypatch, capsys):
        commands: list[list[str]] = []
        monkeypatch.setattr(release, "run", make_fake_run(commands))

        result = main(["release", "minor"])

        assert result == 1
        out, err = capsys.readouterr()
        assert err == "❌ No pyproject.toml or Cargo.toml found\n"

    def test_ci_not_passing(self, in_tmp_path, monkeypatch):
        (in_tmp_path / "pyproject.toml").write_text(
            '[project]\nname = "example"\nversion = "1.2.3"\n'
        )
        commands: list[list[str]] = []
        monkeypatch.setattr(release, "run", make_fake_run(commands))
        monkeypatch.setattr(release, "check_ci_passing", lambda name: False)

        result = main(["release", "minor"])

        assert result == 1

    def test_no_changelog(self, in_tmp_path, monkeypatch, capsys):
        (in_tmp_path / "pyproject.toml").write_text(
            '[project]\nname = "example"\nversion = "1.2.3"\n'
        )
        commands: list[list[str]] = []
        monkeypatch.setattr(release, "run", make_fake_run(commands))
        monkeypatch.setattr(release, "check_ci_passing", lambda name: True)

        result = main(["release", "minor"])

        assert result == 1
        out, err = capsys.readouterr()
        assert err.startswith("❌ No changelog file found")

    def test_pyproject_release_workflow(self, in_tmp_path, monkeypatch, capsys):
        (in_tmp_path / "pyproject.toml").write_text(
            '[project]\nname = "example"\nversion = "1.2.3"\n'
        )
        (in_tmp_path / "uv.lock").write_text("")
        (in_tmp_path / "CHANGELOG.rst").write_text(
            TITLE + "Unreleased\n----------\n\n* An entry.\n"
        )
        (in_tmp_path / ".github/workflows").mkdir(parents=True)
        (in_tmp_path / ".github/workflows/main.yml").write_text(
            "jobs:\n  release:\n    ...\n"
        )
        commands: list[list[str]] = []
        monkeypatch.setattr(release, "run", make_fake_run(commands))
        monkeypatch.setattr(release, "check_ci_passing", lambda name: True)

        result = main(["release", "minor"])

        assert result == 0
        assert (in_tmp_path / "pyproject.toml").read_text() == (
            '[project]\nname = "example"\nversion = "1.3.0"\n'
        )
        today = dt.date.today().isoformat()
        assert (in_tmp_path / "CHANGELOG.rst").read_text() == (
            TITLE + f"1.3.0 ({today})\n" + "-" * len(f"1.3.0 ({today})") + "\n\n"
            "* An entry.\n"
        )
        assert ["uv", "lock"] in commands
        assert [
            "git",
            "commit",
            "--message",
            "Version 1.3.0",
            "--",
            "pyproject.toml",
            "uv.lock",
            "CHANGELOG.rst",
        ] in commands
        assert ["git", "push", "origin", "main"] in commands
        assert [
            "git",
            "tag",
            "--annotate",
            "1.3.0",
            "--message",
            "Version 1.3.0",
        ] in commands
        assert ["git", "push", "--tags", "origin", "1.3.0"] in commands
        assert not any(c[0] == "uvx" for c in commands)

    def test_pyproject_local_build(self, in_tmp_path, monkeypatch):
        (in_tmp_path / "pyproject.toml").write_text(
            '[project]\nname = "example"\nversion = "1.2.3"\n'
        )
        (in_tmp_path / "CHANGELOG.rst").write_text(
            TITLE + "Unreleased\n----------\n\n* An entry.\n"
        )
        commands: list[list[str]] = []
        monkeypatch.setattr(release, "run", make_fake_run(commands))
        monkeypatch.setattr(release, "check_ci_passing", lambda name: True)

        result = main(["release", "minor"])

        assert result == 0
        assert commands[-7][0] == "rm"
        assert commands[-6] == [
            "uvx",
            "--from",
            "build",
            "pyproject-build",
            "--installer",
            "uv",
        ]
        assert commands[-5][:3] == ["uvx", "twine", "check"]
        assert commands[-4][:3] == ["uvx", "twine", "upload"]
        assert commands[-3] == ["git", "push", "origin", "main"]

    def test_pyproject_local_build_sdist_only(self, in_tmp_path, monkeypatch):
        (in_tmp_path / "pyproject.toml").write_text(
            '[project]\nname = "example"\nversion = "1.2.3"\n'
        )
        (in_tmp_path / ".github/workflows").mkdir(parents=True)
        (in_tmp_path / ".github/workflows/main.yml").write_text("jobs:\n  tests:\n")
        commands: list[list[str]] = []
        monkeypatch.setattr(release, "run", make_fake_run(commands))
        monkeypatch.setattr(release, "check_ci_passing", lambda name: True)

        result = main(["release", "patch", "--sdist-only", "--skip-changelog"])

        assert result == 0
        assert (in_tmp_path / "pyproject.toml").read_text() == (
            '[project]\nname = "example"\nversion = "1.2.4"\n'
        )
        assert [
            "uvx",
            "--from",
            "build",
            "pyproject-build",
            "--installer",
            "uv",
            "--sdist",
        ] in commands

    def test_cargo(self, in_tmp_path, monkeypatch):
        (in_tmp_path / "Cargo.toml").write_text(
            '[package]\nname = "example"\nversion = "1.2.3"\n'
        )
        (in_tmp_path / ".github/workflows").mkdir(parents=True)
        (in_tmp_path / ".github/workflows/main.yml").write_text(
            "jobs:\n  release:\n    ...\n"
        )
        commands: list[list[str]] = []
        monkeypatch.setattr(release, "run", make_fake_run(commands))
        monkeypatch.setattr(release, "check_ci_passing", lambda name: True)

        result = main(["release", "major", "--skip-changelog"])

        assert result == 0
        assert (in_tmp_path / "Cargo.toml").read_text() == (
            '[package]\nname = "example"\nversion = "2.0.0"\n'
        )
        assert ["cargo", "check"] in commands
        assert [
            "git",
            "commit",
            "--message",
            "Version 2.0.0",
            "--",
            "Cargo.toml",
            "Cargo.lock",
        ] in commands


class TestBumpVersion:
    def test_major(self):
        assert release.bump_version(Version("1.2.3"), "major") == "2.0.0"

    def test_minor(self):
        assert release.bump_version(Version("1.2.3"), "minor") == "1.3.0"

    def test_patch(self):
        assert release.bump_version(Version("1.2.3"), "patch") == "1.2.4"


class TestReplaceVersionLine:
    def test_pyproject(self, tmp_path):
        path = tmp_path / "pyproject.toml"
        path.write_text('[project]\nname = "example"\nversion = "1.2.3"\n')

        release.replace_version_line(path, "1.3.0")

        assert path.read_text() == '[project]\nname = "example"\nversion = "1.3.0"\n'

    def test_only_first_occurrence(self, tmp_path):
        path = tmp_path / "Cargo.toml"
        path.write_text(
            '[package]\nversion = "1.2.3"\n\n[dependencies.example]\nversion = "4.5.6"\n'
        )

        release.replace_version_line(path, "1.3.0")

        assert path.read_text() == (
            '[package]\nversion = "1.3.0"\n\n[dependencies.example]\nversion = "4.5.6"\n'
        )


def make_ci_fake_run(suites: list[dict[str, Any]]) -> Callable[..., SimpleNamespace]:
    payload = {"data": {"repository": {"object": {"checkSuites": {"nodes": suites}}}}}

    def fake_run(command: list[str], **kwargs: Any) -> SimpleNamespace:
        if command[:2] == ["git", "rev-parse"]:
            stdout = "abc123\n"
        else:
            assert command[:3] == ["gh", "api", "graphql"]
            stdout = json.dumps(payload)
        return SimpleNamespace(stdout=stdout)

    return fake_run


def make_suite(
    app_name: str | None,
    conclusion: str | None,
    check_runs: list[dict[str, str]] | None = None,
    status: str = "COMPLETED",
) -> dict[str, Any]:
    return {
        "creator": None,
        "resourcePath": "/example",
        "status": status,
        "app": {"name": app_name} if app_name is not None else None,
        "conclusion": conclusion,
        "checkRuns": {"nodes": check_runs if check_runs is not None else []},
    }


class TestCheckCiPassing:
    def test_no_check_suites(self, monkeypatch, capsys):
        monkeypatch.setattr(release, "run", make_ci_fake_run([]))

        result = release.check_ci_passing("example")

        assert result is False
        out, err = capsys.readouterr()
        assert err.startswith("❌ No check suites found")

    def test_success(self, monkeypatch):
        suites = [
            make_suite(
                "GitHub Actions",
                "SUCCESS",
                check_runs=[{"name": "tests", "conclusion": "SUCCESS"}],
            ),
            # Filtered: Dependabot allowed to fail
            make_suite(
                "GitHub Actions",
                "FAILURE",
                check_runs=[{"name": "Dependabot", "conclusion": "FAILURE"}],
            ),
            # Filtered: Claude just does review
            make_suite("Claude", None),
            # No app, still counted
            make_suite(None, "SUCCESS"),
        ]
        monkeypatch.setattr(release, "run", make_ci_fake_run(suites))

        result = release.check_ci_passing("example")

        assert result is True

    def test_success_pytest_randomly_ignored_apps(self, monkeypatch):
        suites = [
            make_suite("GitHub Actions", "SUCCESS"),
            # Filtered: apps from the pytest-dev organization configuration
            make_suite("AppVeyor", "FAILURE"),
            make_suite("Travis CI", None),
        ]
        monkeypatch.setattr(release, "run", make_ci_fake_run(suites))

        result = release.check_ci_passing("pytest-randomly")

        assert result is True

    def test_failure(self, monkeypatch, capsys):
        suites = [
            make_suite(
                "GitHub Actions",
                "FAILURE",
                check_runs=[
                    {"name": "tests", "conclusion": "FAILURE"},
                    {"name": "lint", "conclusion": "SUCCESS"},
                ],
            ),
            make_suite("Read the Docs Community", None, status="IN_PROGRESS"),
        ]
        monkeypatch.setattr(release, "run", make_ci_fake_run(suites))

        result = release.check_ci_passing("example")

        assert result is False
        out, err = capsys.readouterr()
        assert "❌ Not all checks are successful:" in err
        assert "GitHub Actions - COMPLETED / FAILURE" in err
        assert "tests: FAILURE" in err
        assert "lint: SUCCESS" in err
        assert "Read the Docs Community - IN_PROGRESS / None" in err
        assert "(No specific runs.)" in err

from __future__ import annotations

import time

import pytest

from repo_tool import gitutils
from repo_tool.commands import upgrade_dependencies
from repo_tool.main import main


class TestRunCommand:
    def test_uncommitted_changes(self, monkeypatch, capsys):
        monkeypatch.setattr(gitutils, "uncommitted_changes", lambda: True)

        result = main(["upgrade-dependencies"])

        assert result == 1
        out, err = capsys.readouterr()
        assert err == "❌ Uncommitted changes.\n"

    def test_branch_already_exists(self, monkeypatch, capsys):
        monkeypatch.setattr(gitutils, "uncommitted_changes", lambda: False)
        monkeypatch.setattr(gitutils, "default_branch", lambda: "main")
        monkeypatch.setattr(gitutils, "branch_exists", lambda name: True)
        commands = []
        monkeypatch.setattr(
            upgrade_dependencies,
            "run",
            lambda command, **kwargs: commands.append(command),
        )

        result = main(["upgrade-dependencies"])

        assert result == 0
        assert commands == [
            ["git", "switch", "main"],
            ["git", "pull"],
        ]
        out, err = capsys.readouterr()
        assert out == "Branch upgrade_dependencies already exists.\n"

    def test_no_changes(self, tmp_path, monkeypatch, capsys):
        monkeypatch.chdir(tmp_path)
        monkeypatch.setattr(gitutils, "uncommitted_changes", lambda: False)
        monkeypatch.setattr(gitutils, "default_branch", lambda: "master")
        monkeypatch.setattr(gitutils, "branch_exists", lambda name: False)
        commands = []
        monkeypatch.setattr(
            upgrade_dependencies,
            "run",
            lambda command, **kwargs: commands.append(command),
        )

        result = main(["upgrade-dependencies"])

        assert result == 0
        assert commands == [
            ["git", "switch", "master"],
            ["git", "pull"],
        ]
        out, err = capsys.readouterr()
        assert out == "No changes.\n"

    def test_changes(self, tmp_path, monkeypatch, capsys):
        monkeypatch.chdir(tmp_path)
        (tmp_path / "uv.lock").write_text("")
        dirty_results = iter([False, True])
        monkeypatch.setattr(
            gitutils, "uncommitted_changes", lambda: next(dirty_results)
        )
        monkeypatch.setattr(gitutils, "default_branch", lambda: "main")
        monkeypatch.setattr(gitutils, "branch_exists", lambda name: False)
        commands = []
        monkeypatch.setattr(
            upgrade_dependencies,
            "run",
            lambda command, **kwargs: commands.append(command),
        )
        monkeypatch.setattr(time, "sleep", lambda seconds: None)

        result = main(["upgrade-dependencies"])

        assert result == 0
        assert commands == [
            ["git", "switch", "main"],
            ["git", "pull"],
            ["uv", "lock", "--upgrade"],
            ["git", "switch", "-c", "upgrade_dependencies"],
            ["git", "commit", "--all", "--message", "Upgrade dependencies"],
            ["git", "push", "--set-upstream", "origin", "upgrade_dependencies"],
            ["gh", "pr", "create", "--fill"],
            [
                "gh",
                "pr",
                "merge",
                "--squash",
                "--delete-branch",
                "--auto",
                "upgrade_dependencies",
            ],
        ]


class TestUpgradeRustToolchain:
    @pytest.fixture(autouse=True)
    def fetch_1_90(self, monkeypatch):
        monkeypatch.setattr(
            upgrade_dependencies, "fetch_latest_rust_version", lambda: "1.90.0"
        )

    def test_toolchain_only(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        toolchain = tmp_path / "rust-toolchain.toml"
        toolchain.write_text('[toolchain]\nchannel = "1.88"\n')

        upgrade_dependencies.upgrade_rust_toolchain()

        assert toolchain.read_text() == '[toolchain]\nchannel = "1.90"\n'

    def test_unpublished_package_msrv(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        toolchain = tmp_path / "rust-toolchain.toml"
        toolchain.write_text('[toolchain]\nchannel = "1.88"\n')
        cargo = tmp_path / "Cargo.toml"
        cargo.write_text(
            '[package]\nname = "example"\npublish = false\nrust-version = "1.88"\n'
        )

        upgrade_dependencies.upgrade_rust_toolchain()

        assert toolchain.read_text() == '[toolchain]\nchannel = "1.90"\n'
        assert cargo.read_text() == (
            '[package]\nname = "example"\npublish = false\nrust-version = "1.90"\n'
        )

    def test_published_package_msrv_untouched(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        toolchain = tmp_path / "rust-toolchain.toml"
        toolchain.write_text('[toolchain]\nchannel = "1.88"\n')
        cargo = tmp_path / "Cargo.toml"
        cargo.write_text('[package]\nname = "example"\nrust-version = "1.88"\n')

        upgrade_dependencies.upgrade_rust_toolchain()

        assert cargo.read_text() == (
            '[package]\nname = "example"\nrust-version = "1.88"\n'
        )

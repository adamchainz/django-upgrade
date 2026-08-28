from __future__ import annotations

import pytest
from packaging.version import Version

from repo_tool import gitutils
from repo_tool.commands import release
from repo_tool.main import main


class TestRunCommand:
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

    def test_no_package_metadata(self, tmp_path, monkeypatch, capsys):
        monkeypatch.chdir(tmp_path)
        monkeypatch.setattr(gitutils, "uncommitted_changes", lambda: False)
        monkeypatch.setattr(gitutils, "default_branch", lambda: "main")

        def fake_run(command, **kwargs):
            class Proc:
                stdout = ""

            if command[:2] == ["git", "rev-parse"] and "--show-toplevel" in command:
                Proc.stdout = "./\n"
            elif command[:2] == ["git", "rev-list"]:
                Proc.stdout = "0\n"
            return Proc()

        monkeypatch.setattr(release, "run", fake_run)

        result = main(["release", "minor"])

        assert result == 1
        out, err = capsys.readouterr()
        assert err == "❌ No pyproject.toml or Cargo.toml found\n"


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

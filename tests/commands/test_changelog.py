from __future__ import annotations

import pytest

from repo_tool.main import main

TITLE = "=========\nChangelog\n=========\n\n"


@pytest.fixture(autouse=True)
def in_tmp_path(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    return tmp_path


class TestAppend:
    def test_no_subcommand(self):
        with pytest.raises(SystemExit) as excinfo:
            main(["changelog"])

        assert excinfo.value.code == 2

    def test_no_changelog(self, capsys):
        result = main(["changelog", "append", "Support Python 3.15."])

        assert result == 1
        out, err = capsys.readouterr()
        assert err.startswith("❌ No changelog file found")

    def test_parse_error(self, in_tmp_path, capsys):
        (in_tmp_path / "CHANGELOG.rst").write_text("Not a changelog.\n")

        result = main(["changelog", "append", "Support Python 3.15."])

        assert result == 1
        out, err = capsys.readouterr()
        assert err == "❌ Changelog title not found.\n"

    def test_success(self, in_tmp_path, capsys):
        path = in_tmp_path / "CHANGELOG.rst"
        path.write_text(TITLE + "1.0.0 (2024-01-01)\n------------------\n\n* First.\n")

        result = main(["changelog", "append", "Support Python 3.15."])

        assert result == 0
        out, err = capsys.readouterr()
        assert out == "✅ Added entry to CHANGELOG.rst\n"
        assert path.read_text() == (
            TITLE
            + "Unreleased\n----------\n\n* Support Python 3.15.\n\n"
            + "1.0.0 (2024-01-01)\n------------------\n\n* First.\n"
        )

    def test_success_docs_changelog(self, in_tmp_path, capsys):
        (in_tmp_path / "docs").mkdir()
        path = in_tmp_path / "docs/changelog.rst"
        path.write_text(TITLE + "Unreleased\n----------\n\n* Existing.\n")

        result = main(["changelog", "append", "Support Python 3.15."])

        assert result == 0
        out, err = capsys.readouterr()
        assert out == "✅ Added entry to docs/changelog.rst\n"
        assert path.read_text() == (
            TITLE + "Unreleased\n----------\n\n* Existing.\n* Support Python 3.15.\n"
        )

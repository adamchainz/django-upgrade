from __future__ import annotations

import datetime as dt

import pytest

from repo_tool import changelogs


class TestFind:
    def test_none(self, tmp_path):
        with pytest.raises(changelogs.ChangelogNotFound):
            changelogs.find(tmp_path)

    def test_changelog_rst(self, tmp_path):
        (tmp_path / "CHANGELOG.rst").write_text("...\n")

        result = changelogs.find(tmp_path)

        assert result == tmp_path / "CHANGELOG.rst"

    def test_docs_changelog_rst(self, tmp_path):
        (tmp_path / "docs").mkdir()
        (tmp_path / "docs/changelog.rst").write_text("...\n")

        result = changelogs.find(tmp_path)

        assert result == tmp_path / "docs/changelog.rst"

    def test_docs_changelog_rst_preferred(self, tmp_path):
        (tmp_path / "docs").mkdir()
        (tmp_path / "docs/changelog.rst").write_text("...\n")
        (tmp_path / "CHANGELOG.rst").write_text("...\n")

        result = changelogs.find(tmp_path)

        assert result == tmp_path / "docs/changelog.rst"

    def test_default_root(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        (tmp_path / "CHANGELOG.rst").write_text("...\n")

        result = changelogs.find()

        assert result.name == "CHANGELOG.rst"


TITLE = "=========\nChangelog\n=========\n\n"


class TestAddEntry:
    def test_no_title(self):
        with pytest.raises(changelogs.ChangelogParseError) as excinfo:
            changelogs.add_entry("Some other file.\n", "Support Python 3.15.")

        assert excinfo.value.message == "Changelog title not found."

    def test_no_unreleased_section(self):
        content = TITLE + "1.0.0 (2024-01-01)\n------------------\n\n* First.\n"

        result = changelogs.add_entry(content, "Support Python 3.15.")

        assert result == (
            TITLE
            + "Unreleased\n----------\n\n"
            + "* Support Python 3.15.\n\n"
            + "1.0.0 (2024-01-01)\n------------------\n\n* First.\n"
        )

    def test_existing_unreleased_section(self):
        content = (
            TITLE
            + "Unreleased\n----------\n\n* Existing.\n\n"
            + "1.0.0 (2024-01-01)\n------------------\n\n* First.\n"
        )

        result = changelogs.add_entry(content, "Support Python 3.15.")

        assert result == (
            TITLE
            + "Unreleased\n----------\n\n* Existing.\n* Support Python 3.15.\n\n"
            + "1.0.0 (2024-01-01)\n------------------\n\n* First.\n"
        )

    def test_existing_pending_section(self):
        content = (
            TITLE
            + "Pending\n-------\n\n* Existing.\n\n"
            + "1.0.0 (2024-01-01)\n------------------\n\n* First.\n"
        )

        result = changelogs.add_entry(content, "Support Python 3.15.")

        assert result == (
            TITLE
            + "Pending\n-------\n\n* Existing.\n* Support Python 3.15.\n\n"
            + "1.0.0 (2024-01-01)\n------------------\n\n* First.\n"
        )

    def test_unreleased_section_only(self):
        content = TITLE + "Unreleased\n----------\n\n* Existing.\n"

        result = changelogs.add_entry(content, "Support Python 3.15.")

        assert result == (
            TITLE + "Unreleased\n----------\n\n* Existing.\n* Support Python 3.15.\n"
        )

    def test_no_versions(self):
        content = TITLE + "Unreleased\n----------\n\n* Existing.\n"

        result = changelogs.add_entry(content, "* Already bulleted.")

        assert result == (
            TITLE + "Unreleased\n----------\n\n* Existing.\n* Already bulleted.\n"
        )


class TestStartVersion:
    date = dt.date(2024, 1, 2)

    def test_no_title(self):
        with pytest.raises(changelogs.ChangelogParseError) as excinfo:
            changelogs.start_version("Some other file.\n", "1.1.0", self.date)

        assert excinfo.value.message == "Changelog title not found."

    def test_malformed_unreleased_heading(self):
        content = TITLE + "Unreleased\n---\n\n* An entry.\n"

        with pytest.raises(changelogs.ChangelogParseError) as excinfo:
            changelogs.start_version(content, "1.1.0", self.date)

        assert excinfo.value.message == "Malformed 'Unreleased' section heading."

    def test_no_entries(self):
        content = TITLE + "1.0.0 (2024-01-01)\n------------------\n\n* First.\n"

        with pytest.raises(changelogs.ChangelogParseError) as excinfo:
            changelogs.start_version(content, "1.1.0", self.date)

        assert excinfo.value.message == "No unreleased changelog entries found."

    def test_unreleased(self):
        content = (
            TITLE
            + "Unreleased\n----------\n\n* An entry.\n\n"
            + "1.0.0 (2024-01-01)\n------------------\n\n* First.\n"
        )

        result = changelogs.start_version(content, "1.1.0", self.date)

        assert result == (
            TITLE
            + "1.1.0 (2024-01-02)\n------------------\n\n* An entry.\n\n"
            + "1.0.0 (2024-01-01)\n------------------\n\n* First.\n"
        )

    def test_pending(self):
        content = (
            TITLE
            + "Pending\n-------\n\n* An entry.\n\n"
            + "1.0.0 (2024-01-01)\n------------------\n\n* First.\n"
        )

        result = changelogs.start_version(content, "1.1.0", self.date)

        assert result == (
            TITLE
            + "1.1.0 (2024-01-02)\n------------------\n\n* An entry.\n\n"
            + "1.0.0 (2024-01-01)\n------------------\n\n* First.\n"
        )

    def test_no_unreleased_heading(self):
        content = TITLE + "* An entry.\n"

        result = changelogs.start_version(content, "1.1.0", self.date)

        assert result == (
            TITLE + "1.1.0 (2024-01-02)\n------------------\n\n* An entry.\n"
        )

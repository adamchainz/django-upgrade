from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from repo_tool import gitutils


def init_repo(path: Path, branch: str) -> None:
    subprocess.run(
        ["git", "init", "--quiet", "--initial-branch", branch],
        check=True,
        cwd=path,
    )
    subprocess.run(
        ["git", "config", "user.email", "test@example.com"], check=True, cwd=path
    )
    subprocess.run(["git", "config", "user.name", "Test"], check=True, cwd=path)
    (path / "file.txt").write_text("hello\n")
    subprocess.run(["git", "add", "file.txt"], check=True, cwd=path)
    subprocess.run(
        ["git", "commit", "--quiet", "--message", "Initial"], check=True, cwd=path
    )


@pytest.fixture
def git_repo(tmp_path, monkeypatch):
    init_repo(tmp_path, "main")
    monkeypatch.chdir(tmp_path)
    return tmp_path


class TestUncommittedChanges:
    def test_clean(self, git_repo):
        assert gitutils.uncommitted_changes() is False

    def test_dirty(self, git_repo):
        (git_repo / "file.txt").write_text("changed\n")

        assert gitutils.uncommitted_changes() is True


class TestDefaultBranch:
    def test_main(self, git_repo):
        assert gitutils.default_branch() == "main"

    def test_master(self, tmp_path, monkeypatch):
        init_repo(tmp_path, "master")
        monkeypatch.chdir(tmp_path)

        assert gitutils.default_branch() == "master"


class TestBranchExists:
    def test_exists(self, git_repo):
        assert gitutils.branch_exists("main") is True

    def test_does_not_exist(self, git_repo):
        assert gitutils.branch_exists("other") is False

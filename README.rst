=========
repo-tool
=========

.. image:: https://img.shields.io/github/actions/workflow/status/adamchainz/repo-tool/main.yml.svg?branch=main&style=for-the-badge
   :target: https://github.com/adamchainz/repo-tool/actions?workflow=CI

.. image:: https://img.shields.io/badge/Coverage-100%25-success?style=for-the-badge
  :target: https://github.com/adamchainz/repo-tool/actions?workflow=CI

.. image:: https://img.shields.io/badge/code%20style-black-000000.svg?style=for-the-badge
   :target: https://github.com/psf/black

.. image:: https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit&logoColor=white&style=for-the-badge
   :target: https://github.com/pre-commit/pre-commit
   :alt: pre-commit

Multitool for maintaining many repositories.

``repo-tool`` bundles maintenance operations that apply across many
repositories into one CLI with subcommands.
It assumes the conventions used in my (Adam Johnson's) repositories: ``uv``
for Python packaging, a reStructuredText changelog in ``docs/changelog.rst``
or ``CHANGELOG.rst``, GitHub with the ``gh`` CLI, and GitHub Actions with a
tag-triggered release workflow in ``.github/workflows/main.yml``.

Installation
============

Use **uv** to run the latest version directly from GitHub:

.. code-block:: sh

    uvx --from git+https://github.com/adamchainz/repo-tool repo-tool --help

…or install it as a tool:

.. code-block:: sh

    uv tool install git+https://github.com/adamchainz/repo-tool

Python 3.11 to 3.15 supported.

Commands
========

Run ``repo-tool <command> --help`` for full options.

``changelog append``
--------------------

Add an entry to the unreleased section of the current repository's changelog,
creating the section if it does not exist:

.. code-block:: console

    $ repo-tool changelog append 'Support Python 3.15.'
    ✅ Added entry to docs/changelog.rst

The changelog file is found at ``docs/changelog.rst`` or ``CHANGELOG.rst``,
and the entry is appended to the ``Unreleased`` (or ``Pending``) section,
which is created if missing.
This is useful in scripts that apply a change across many repositories, so
each one gets a changelog entry recorded in the right place.

``release``
-----------

Release the package in the current repository:

.. code-block:: console

    $ repo-tool release minor

This:

1. Checks the working tree is clean, on an up-to-date default branch, with
   passing CI (via ``gh``), and no tag on the current commit.
2. Bumps the version in ``pyproject.toml`` or ``Cargo.toml`` per the given
   ``major``/``minor``/``patch`` argument.
3. Retitles the changelog's unreleased section as the new version, dated
   today (skip with ``--skip-changelog``).
4. Commits, and, if there's no ``release:`` job in
   ``.github/workflows/main.yml``, builds and uploads to PyPI locally
   (``--sdist-only`` to limit to an sdist).
5. Pushes, tags the release, and pushes the tag, which triggers the release
   workflow, where one exists.

``upgrade-dependencies``
------------------------

Upgrade the current repository's pinned dependencies and push the changes as
an auto-merging PR:

.. code-block:: console

    $ repo-tool upgrade-dependencies

This upgrades ``uv.lock``, the pinned Rust version in
``rust-toolchain.toml`` (plus MSRV for unpublished packages), and
``Cargo.lock``, where those files exist.
Any changes are committed on an ``upgrade_dependencies`` branch and pushed as
a PR set to squash-merge automatically when checks pass, via ``gh``.

Adding commands
===============

Each command lives in a module in ``src/repo_tool/commands/`` defining
``add_arguments()``, registered in ``repo_tool.main``.
Shared helpers live in ``repo_tool.changelogs`` and ``repo_tool.gitutils``.

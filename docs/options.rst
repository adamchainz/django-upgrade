=======
Options
=======

.. option:: --target-version

The version of Django to target, in the format ``<major>.<minor>``.
django-upgrade enables all of its fixers for versions up to and including the target version.
See the list of available versions with ``django-upgrade --help``.

When ``--target-version`` is not specified, django-upgrade attempts to detect the target version from a ``pyproject.toml`` in the current directory.
If found, it attempts to parse your current minimum-supported Django version from |project.dependencies|__, supporting formats like ``django>=5.2,<6.0``.
When available, it reports:

.. |project.dependencies| replace:: ``project.dependencies``
__ https://packaging.python.org/en/latest/specifications/pyproject-toml/#dependencies-optional-dependencies

.. code-block:: sh

    $ django-upgrade example.py
    Detected Django version from pyproject.toml: 5.2
    ...

If this doesn’t work, ``--target-version`` defaults to 2.2, the oldest supported Django version when django-upgrade was created.

.. option:: --exit-zero-even-if-changed

Exit with a zero return code even if files have changed.
By default, django-upgrade uses the failure return code 1 if it changes any files, which may stop scripts or CI pipelines.

.. option:: --only <fixer_name>

Run only the named fixer (names are documented below).
The fixer must still be enabled by :option:`--target-version`.
Select multiple fixers with multiple ``--only`` options.

For example:

.. code-block:: sh

    django-upgrade --target-version 5.2 --only admin_allow_tags --only admin_decorators example/core/admin.py

.. option:: --skip <fixer_name>

Skip the named fixer.
Skip multiple fixers with multiple ``--skip`` options.

For example:

.. code-block:: sh

    django-upgrade --target-version 5.2 --skip admin_register example/core/admin.py

.. option:: --list-fixers

List all available fixers’ names and then exit.
All other options are ignored when listing fixers.

For example:

.. code-block:: sh

    django-upgrade --list-fixers

.. option:: --check

Show files that would be changed, but don’t modify them.

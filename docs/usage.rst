=====
Usage
=====

``django-upgrade`` is a commandline tool that rewrites files in place to avoid ``DeprecationWarning``\s and use some new features.
For example:

.. code-block:: sh

    django-upgrade example/core/models.py example/settings.py

``django-upgrade`` focuses on upgrading your code and not on making it look nice.
Run django-upgrade before formatters like `Black <https://black.readthedocs.io/en/stable/>`__.

Some of django-upgrade’s fixers make changes to models that need migrations:

* ``index_together``
* ``null_boolean_field``

Add a `test for pending migrations <https://adamj.eu/tech/2024/06/23/django-test-pending-migrations/>`__ to ensure that you do not miss these.

``django-upgrade`` does not have any ability to recurse through directories.
Use the pre-commit integration, globbing, or another technique for applying to many files.
Some fixers depend on the names of containing directories to activate, so ensure you run django-upgrade with paths relative to the root of your project.
For example, |with git ls-files pipe xargs|_:

.. |with git ls-files pipe xargs| replace:: with ``git ls-files | xargs``
.. _with git ls-files pipe xargs: https://adamj.eu/tech/2022/03/09/how-to-run-a-command-on-many-files-in-your-git-repository/

.. code-block:: sh

    git ls-files -z -- '*.py' | xargs -0r django-upgrade --target-version 5.2

…or PowerShell’s |ForEach-Object|__:

.. |ForEach-Object| replace:: ``ForEach-Object``
__ https://learn.microsoft.com/en-us/powershell/module/microsoft.powershell.core/foreach-object

.. code-block:: powershell

    git ls-files -- '*.py' | %{django-upgrade --target-version 5.2 $_}

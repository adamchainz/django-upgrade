============
Installation
============

Requirements
------------

Python 3.9 to 3.14 supported.

(Python 3.12+ is required to correctly apply fixes within f-strings.)

Installation
------------

Use **pip**:

.. code-block:: sh

    python -m pip install django-upgrade

pre-commit hook
---------------

You can also install django-upgrade as a `pre-commit <https://pre-commit.com/>`__ hook.
Add the following to the ``repos`` section of your ``.pre-commit-config.yaml`` file (`docs <https://pre-commit.com/#plugins>`__), above any code formatters (such as Black):

.. code-block:: yaml

    -   repo: https://github.com/adamchainz/django-upgrade
        rev: ""  # replace with latest tag on GitHub
        hooks:
        -   id: django-upgrade

django-upgrade attempts to parse your current Django version from ``pyproject.toml``.
If this doesn’t work for you, specify your target version with the ``--target-version`` option:

.. code-block:: diff

     -   id: django-upgrade
    +    args: [--target-version, "5.2"]   # Replace with Django version

Now, upgrade your entire project:

.. code-block:: sh

    pre-commit run django-upgrade --all-files

Commit any changes.
In the process, your other hooks will run, potentially reformatting django-upgrade’s changes to match your project’s code style.

Keep the hook installed in order to upgrade all code added to your project.
pre-commit’s ``autoupdate`` command will also let you take advantage of future django-upgrade features.

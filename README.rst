==============
django-upgrade
==============

.. image:: https://img.shields.io/github/workflow/status/adamchainz/django-upgrade/CI/main?style=for-the-badge
   :target: https://github.com/adamchainz/django-upgrade/actions?workflow=CI

.. image:: https://img.shields.io/codecov/c/github/adamchainz/django-upgrade/main?style=for-the-badge
  :target: https://app.codecov.io/gh/adamchainz/django-upgrade

.. image:: https://img.shields.io/pypi/v/django-upgrade.svg?style=for-the-badge
   :target: https://pypi.org/project/django-upgrade/

.. image:: https://img.shields.io/badge/code%20style-black-000000.svg?style=for-the-badge
   :target: https://github.com/psf/black

.. image:: https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit&logoColor=white&style=for-the-badge
   :target: https://github.com/pre-commit/pre-commit
   :alt: pre-commit

Automatically upgrade your Django projects.

Installation
============

Use **pip**:

.. code-block:: sh

    python -m pip install django-upgrade

Python 3.6 to 3.9 supported.

Or with `pre-commit <https://pre-commit.com/>`__ in the ``repos`` section of your ``.pre-commit-config.yaml`` file (`docs <https://pre-commit.com/#plugins>`__):

.. code-block:: yaml

    -   repo: https://github.com/adamchainz/django-upgrade
        rev: ''  # replace with latest tag on GitHub
        hooks:
        -   id: django-upgrade
            args: [--target-version, "3.2"]   # Replace with Django version

Works best before any reformatters such as `isort <https://isort.readthedocs.io/>`__ or `Black <https://black.readthedocs.io/en/stable/>`__.

----

**Are your tests slow?**
Check out my book `Speed Up Your Django Tests <https://gumroad.com/l/suydt>`__ which covers loads of best practices so you can write faster, more accurate tests.

----

Usage
=====

``django-upgrade`` is a commandline tool that rewrites files in place.
Pass your Django version as ``<major>.<minor>`` with ``--target-version`` and the fixers will rewrite code not to trigger ``DeprecationWarning`` on that version of Django.
For example:

.. code-block:: sh

    django-upgrade --target-version 3.2 example/core/models.py example/settings.py

For more on usage run ``django-upgrade --help``.
The full list of fixers is below.

History
=======

`django-codemod <https://django-codemod.readthedocs.io/en/latest/>`__ is a pre-existing, more complete Django auto-upgrade tool, written by Bruno Alla.
Unfortunately its underlying library `LibCST <https://pypi.org/project/libcst/>`__ is particularly slow, making it annoying to run django-codemod on every commit and in CI.
Additionally LibCST only advertises support up to Python 3.8 (at time of writing).

django-upgrade is an experiment in reimplementing such a tool using the same techniques as the fantastic `pyupgrade <https://github.com/asottile/pyupgrade>`__.
The tool leans on the standard library’s `ast <https://docs.python.org/3/library/ast.html>`__ and `tokenize <https://docs.python.org/3/library/tokenize.html>`__ modules, the latter via the `tokenize-rt wrapper <https://github.com/asottile/tokenize-rt>`__.
This means it will always be fast and support the latest versions of Python.

For a quick benchmark: running django-codemod against a medium Django repository with 153k lines of Python takes 133 seconds.
pyupgrade and django-upgrade both take less than 0.5 seconds.

Fixers
======

Django 2.2
----------

Based on the `Django 2.2 release notes <https://docs.djangoproject.com/en/2.2/releases/2.2/#features-deprecated-in-2-2>`__.

``django.core.paginator``
~~~~~~~~~~~~~~~~~~~~~~~~~

* ``QuerySetPaginator`` → ``Paginator``

.. code-block:: diff

    -from django.core.paginator import QuerySetPaginator
    +from django.core.paginator import Paginator

    -QuerySetPaginator(...)
    +Paginator(...)


``django.utils.timezone``
~~~~~~~~~~~~~~~~~~~~~~~~~

* ``FixedOffset(x, y)`` → ``timezone(timedelta(minutes=x), y)``
* Will leave code broken with an ``ImportError`` if ``FixedOffset`` is called with (only) ``*args`` or ``**kwargs``.

.. code-block:: diff

    -from django.utils.timezone import FixedOffset
    -FixedOffset(120, "Super time")
    +from datetime import timedelta, timezone
    +timezone(timedelta(minutes=120), "Super time")


Django 3.0
----------

Based on the `Django 3.0 release notes <https://docs.djangoproject.com/en/3.0/releases/3.0/#features-deprecated-in-3-0>`__.

``django.utils.encoding``
~~~~~~~~~~~~~~~~~~~~~~~~~

* ``smart_text()`` → ``smart_str()`` , ``force_text()`` → ``force_str()``
* django-upgrade does not support Python 2 so these names are always replaced.

.. code-block:: diff

    -from django.utils.encoding import force_text, smart_text
    +from django.utils.encoding import force_str, smart_str


    -force_text("yada")
    -smart_text("yada")
    +force_str("yada")
    +smart_str("yada")

Django 3.1
----------

Based on the `Django 3.1 release notes <https://docs.djangoproject.com/en/3.2/releases/3.2/#features-deprecated-in-3-1>`__.

``JSONField``
~~~~~~~~~~~~~

Rewrites:

* ``django.contrib.postgres.fields.JSONField`` → ``django.db.models.JSONField``
* ``django.contrib.postgres.forms.JSONField`` → ``django.forms.JSONField``

.. code-block:: diff

    -from django.contrib.postgres.fields import JSONField
    +from django.db.models import JSONField

``PASSWORD_RESET_TIMEOUT_DAYS``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

* Rewrites the setting ``PASSWORD_RESET_TIMEOUT_DAYS`` → ``PASSWORD_RESET_TIMEOUT``, including multiplication by the number of seconds in a day.
* Settings files are heuristically detected as modules with the word “settings” somewhere in their path.

.. code-block:: diff

    -PASSWORD_RESET_TIMEOUT_DAYS = 4
    +PASSWORD_RESET_TIMEOUT = 60 * 60 * 24 * 4

Django 3.2
----------

Based on the `Django 3.2 release notes <https://docs.djangoproject.com/en/3.2/releases/3.2/#features-deprecated-in-3-2>`__.

``django.core.validators.EmailValidator``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

* Rewrites keyword arguments ``whitelist`` → ``allowlist`` and ``domain_whitelist`` → ``domain_allowlist``.

.. code-block:: diff

     from django.core.validators import EmailValidator

    -EmailValidator(whitelist=["example.com"])
    +EmailValidator(allowlist=["example.com"])
    -EmailValidator(domain_whitelist=["example.org"])
    +EmailValidator(domain_allowlist=["example.org"])

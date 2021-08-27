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

Or with pre-commit in the ``repos`` section of your ``.pre-commit-config.yaml`` file:

.. code-block:: yaml

    -   repo: https://github.com/adamchainz/django-upgrade
        rev: ''  # replace with latest tag on GitHub
        hooks:
        -   id: django-upgrade

----

**Are your tests slow?**
Check out my book `Speed Up Your Django Tests <https://gumroad.com/l/suydt>`__ which covers loads of best practices so you can write faster, more accurate tests.

----

Currently an experimental alternative to `django-codemod <https://django-codemod.readthedocs.io/en/latest/>`__, whose underlying library `LibCST <https://pypi.org/project/libcst/>`__ is relatively slow.

Usage
=====

Run ``django-upgrade --help`` on the commandline for information.

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

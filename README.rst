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

----

**Are your tests slow?**
Check out my book `Speed Up Your Django Tests <https://gumroad.com/l/suydt>`__ which covers loads of best practices so you can write faster, more accurate tests.

----

Currently an experimental alternative to `django-codemod <https://django-codemod.readthedocs.io/en/latest/>`__, whose underlying library `LibCST <https://pypi.org/project/libcst/>`__ is relatively slow.

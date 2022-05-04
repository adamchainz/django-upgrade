==============
django-upgrade
==============

.. image:: https://img.shields.io/github/workflow/status/adamchainz/django-upgrade/CI/main?style=for-the-badge
   :target: https://github.com/adamchainz/django-upgrade/actions?workflow=CI

.. image:: https://img.shields.io/badge/Coverage-100%25-success?style=for-the-badge
  :target: https://github.com/adamchainz/django-upgrade/actions?workflow=CI

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

Python 3.8 to 3.10 supported.

Or with `pre-commit <https://pre-commit.com/>`__ in the ``repos`` section of your ``.pre-commit-config.yaml`` file (`docs <https://pre-commit.com/#plugins>`__):

.. code-block:: yaml

    -   repo: https://github.com/adamchainz/django-upgrade
        rev: ''  # replace with latest tag on GitHub
        hooks:
        -   id: django-upgrade
            args: [--target-version, "3.2"]   # Replace with Django version

----

**Want to improve your code quality?**
Check out my book `Boost Your Django DX <https://adamchainz.gumroad.com/l/byddx>`__ which covers using  pre-commit, django-upgrade, and many other tools.
I wrote django-upgrade whilst working on the book!

----

Usage
=====

``django-upgrade`` is a commandline tool that rewrites files in place.
Pass your Django version as ``<major>.<minor>`` to the ``--target-version`` flag.
The built-in fixers will rewrite your code to avoid some ``DeprecationWarning``\s and use some new features on your Django version.
For example:

.. code-block:: sh

    django-upgrade --target-version 3.2 example/core/models.py example/settings.py

The ``--target-version`` flag defaults to 2.2, the oldest supported version when this project was created.
For more on usage run ``django-upgrade --help``.

``django-upgrade`` focuses on upgrading your code and not on making it look nice.
Run django-upgrade before formatters like `Black <https://black.readthedocs.io/en/stable/>`__.

``django-upgrade`` does not have any ability to recurse through directories.
Use the pre-commit integration, globbing, or another technique for applying to many files such as |with git ls-files pipe xargs|__.

.. |with git ls-files pipe xargs| replace:: with ``git ls-files | xargs``
__ https://adamj.eu/tech/2022/03/09/how-to-run-a-command-on-many-files-in-your-git-repository/

The full list of fixers is documented below.

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

Django 1.9
-----------

`Release Notes <https://github.com/django/django/blob/main/docs/releases/1.9.txt>`__

``on_delete`` argument
~~~~~~~~~~~~~~~~~~~~~~

Add ``on_delete=models.CASCADE`` to ``ForeignKey`` and ``OneToOneField``:

.. code-block:: diff

    -models.ForeignKey("auth.User")
    +models.ForeignKey("auth.User", on_delete=models.CASCADE)

    -models.OneToOneField("auth.User")
    +models.OneToOneField("auth.User", on_delete=models.CASCADE)

Compatibility imports
~~~~~~~~~~~~~~~~~~~~~

Rewrites some compatibility imports:

* ``django.forms.utils.pretty_name`` in ``django.forms.forms``
* ``django.forms.boundfield.BoundField`` in ``django.forms.forms``

Whilst mentioned in the `Django 3.1 release notes <https://docs.djangoproject.com/en/3.1/releases/3.1/#id1>`_, these have been possible since Django 1.9.

.. code-block:: diff

    -from django.forms.forms import pretty_name
    +from django.forms.utils import pretty_name

Django 1.11
-----------

`Release Notes <https://docs.djangoproject.com/en/1.11/releases/1.11/#features-deprecated-in-1-11>`__

Compatibility imports
~~~~~~~~~~~~~~~~~~~~~

Rewrites some compatibility imports:

* ``django.core.exceptions.EmptyResultSet`` in ``django.db.models.query``, ``django.db.models.sql``, and ``django.db.models.sql.datastructures``
* ``django.core.exceptions.FieldDoesNotExist`` in ``django.db.models.fields``

Whilst mentioned in the `Django 3.1 release notes <https://docs.djangoproject.com/en/3.1/releases/3.1/#id1>`_, these have been possible since Django 1.11.

.. code-block:: diff

    -from django.db.models.query import EmptyResultSet
    +from django.core.exceptions import EmptyResultSet

    -from django.db.models.fields import FieldDoesNotExist
    +from django.core.exceptions import FieldDoesNotExist

Django 2.0
----------

`Release Notes <https://docs.djangoproject.com/en/2.0/releases/2.0/#features-deprecated-in-2-0>`__

URL’s
~~~~~

Rewrites imports of ``include()`` and ``url()`` from ``django.conf.urls`` to ``django.urls``.
``url()`` calls using compatible regexes are rewritten to the |new path() syntax|__, otherwise they are converted to call ``re_path()``.

.. |new path() syntax| replace:: new ``path()`` syntax
__ https://docs.djangoproject.com/en/2.0/releases/2.0/#simplified-url-routing-syntax

.. code-block:: diff

    -from django.conf.urls import include, url
    +from django.urls import include, path, re_path

     urlpatterns = [
    -    url(r'^$', views.index, name='index'),
    +    path('', views.index, name='index'),
    -    url(r'^about/$', views.about, name='about'),
    +    path('about/', views.about, name='about'),
    -    url(r'^post/(?P<slug>[-a-zA-Z0-9_]+)/$', views.post, name='post'),
    +    re_path(r'^post/(?P<slug>[w-]+)/$', views.post, name='post'),
    -    url(r'^weblog/', include('blog.urls')),
    +    path('weblog/', include('blog.urls')),
     ]

``lru_cache``
~~~~~~~~~~~~~

Rewrites imports of ``lru_cache`` from ``django.utils.functional`` to use ``functools``.

.. code-block:: diff

    -from django.utils.functional import lru_cache
    +from functools import lru_cache

Django 2.2
----------

`Release Notes <https://docs.djangoproject.com/en/2.2/releases/2.2/#features-deprecated-in-2-2>`__

``HttpRequest.headers``
~~~~~~~~~~~~~~~~~~~~~~~

Rewrites use of ``request.META`` to read HTTP headers to instead use |request.headers|__.

.. |request.headers| replace:: ``request.headers``
__ https://docs.djangoproject.com/en/2.2/ref/request-response/#django.http.HttpRequest.headers

.. code-block:: diff

    -request.META['HTTP_ACCEPT_ENCODING']
    +request.headers['Accept-Encoding']

    -self.request.META.get('HTTP_SERVER', '')
    +self.request.headers.get('Server', '')

``QuerySetPaginator``
~~~~~~~~~~~~~~~~~~~~~

Rewrites deprecated alias ``django.core.paginator.QuerySetPaginator`` to ``Paginator``.

.. code-block:: diff

    -from django.core.paginator import QuerySetPaginator
    +from django.core.paginator import Paginator

    -QuerySetPaginator(...)
    +Paginator(...)


``FixedOffset``
~~~~~~~~~~~~~~~

Rewrites deprecated class ``FixedOffset(x, y))`` to ``timezone(timedelta(minutes=x), y)``

Known limitation: this fixer will leave code broken with an ``ImportError`` if ``FixedOffset`` is called with only ``*args`` or ``**kwargs``.

.. code-block:: diff

    -from django.utils.timezone import FixedOffset
    -FixedOffset(120, "Super time")
    +from datetime import timedelta, timezone
    +timezone(timedelta(minutes=120), "Super time")

``FloatRangeField``
~~~~~~~~~~~~~~~~~~~

Rewrites model and form fields using ``FloatRangeField`` to ``DecimalRangeField``, from the relevant ``django.contrib.postgres`` modules.

.. code-block:: diff

     from django.db.models import Model
    -from django.contrib.postgres.fields import FloatRangeField
    +from django.contrib.postgres.fields import DecimalRangeField

     class MyModel(Model):
    -    my_field = FloatRangeField("My range of numbers")
    +    my_field = DecimalRangeField("My range of numbers")

``TestCase`` class database declarations
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Rewrites the ``allow_database_queries`` and ``multi_db`` attributes of Django’s ``TestCase`` classes to the new ``databases`` attribute.
This only applies in test files, which are heuristically detected as files with either “test” or “tests” somewhere in their path.

Note that this will only rewrite to ``databases = []`` or ``databases = "__all__"``.
With multiple databases you can save some test time by limiting test cases to the databases they require (which is why Django made the change).

.. code-block:: diff

     from django.test import SimpleTestCase

     class MyTests(SimpleTestCase):
    -    allow_database_queries = True
    +    databases = "__all__"

         def test_something(self):
             self.assertEqual(2 * 2, 4)

Django 3.0
----------

`Release Notes <https://docs.djangoproject.com/en/3.0/releases/3.0/#features-deprecated-in-3-0>`__

``django.utils.encoding`` aliases
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Rewrites ``smart_text()`` to ``smart_str()``, and ``force_text()`` to ``force_str()``.

.. code-block:: diff

    -from django.utils.encoding import force_text, smart_text
    +from django.utils.encoding import force_str, smart_str


    -force_text("yada")
    -smart_text("yada")
    +force_str("yada")
    +smart_str("yada")

``django.utils.http`` deprecations
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Rewrites the ``urlquote()``, ``urlquote_plus()``, ``urlunquote()``, and ``urlunquote_plus()`` functions to the ``urllib.parse`` versions.
Also rewrites the internal function ``is_safe_url()`` to ``url_has_allowed_host_and_scheme()``.

.. code-block:: diff

    -from django.utils.http import urlquote
    +from urllib.parse import quote

    -escaped_query_string = urlquote(query_string)
    +escaped_query_string = quote(query_string)

``django.utils.text`` deprecation
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Rewrites ``unescape_entities()`` with the standard library ``html.escape()``.

.. code-block:: diff

    -from django.utils.text import unescape_entities
    +import html

    -unescape_entities("some input string")
    +html.escape("some input string")

``django.utils.translation`` deprecations
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Rewrites the ``ugettext()``, ``ugettext_lazy()``, ``ugettext_noop()``, ``ungettext()``, and ``ungettext_lazy()`` functions to their non-u-prefixed versions.

.. code-block:: diff

    -from django.utils.translation import ugettext as _, ungettext
    +from django.utils.translation import gettext as _, ngettext

    -ungettext("octopus", "octopodes", n)
    +ngettext("octopus", "octopodes", n)

Django 3.1
----------

`Release Notes <https://docs.djangoproject.com/en/3.1/releases/3.1/#features-deprecated-in-3-1>`__

``JSONField``
~~~~~~~~~~~~~

Rewrites imports of ``JSONField`` and related transform classes from those in ``django.contrib.postgres`` to the new all-database versions.
Ignores usage in migration files, since Django kept the old class around to support old migrations.
You will need to make migrations after this fix makes changes to models.

.. code-block:: diff

    -from django.contrib.postgres.fields import JSONField
    +from django.db.models import JSONField

``PASSWORD_RESET_TIMEOUT_DAYS``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Rewrites the setting ``PASSWORD_RESET_TIMEOUT_DAYS`` to ``PASSWORD_RESET_TIMEOUT``, adding the multiplication by the number of seconds in a day.

Settings files are heuristically detected as modules with the whole word “settings” somewhere in their path.
For example ``myproject/settings.py`` or ``myproject/settings/production.py``.

.. code-block:: diff

    -PASSWORD_RESET_TIMEOUT_DAYS = 4
    +PASSWORD_RESET_TIMEOUT = 60 * 60 * 24 * 4

``Signal``
~~~~~~~~~~

Removes the deprecated documentation-only ``providing_args`` argument.

.. code-block:: diff

     from django.dispatch import Signal
    -my_cool_signal = Signal(providing_args=["documented", "arg"])
    +my_cool_signal = Signal()

``get_random_string``
~~~~~~~~~~~~~~~~~~~~~

Injects the now-required ``length`` argument, with its previous default ``12``.

.. code-block:: diff

     from django.utils.crypto import get_random_string
    -key = get_random_string(allowed_chars="01234567899abcdef")
    +key = get_random_string(length=12, allowed_chars="01234567899abcdef")

``NullBooleanField``
~~~~~~~~~~~~~~~~~~~~

Transforms the ``NullBooleanField()`` model field to ``BooleanField(null=True)``.
Ignores usage in migration files, since Django kept the old class around to support old migrations.
You will need to make migrations after this fix makes changes to models.

.. code-block:: diff

    -from django.db.models import Model, NullBooleanField
    +from django.db.models import Model, BooleanField

     class Book(Model):
    -    valuable = NullBooleanField("Valuable")
    +    valuable = BooleanField("Valuable", null=True)

Django 3.2
----------

`Release Notes <https://docs.djangoproject.com/en/3.2/releases/3.2/#features-deprecated-in-3-2>`__

``EmailValidator``
~~~~~~~~~~~~~~~~~~

Rewrites keyword arguments to their new names: ``whitelist`` to ``allowlist``, and ``domain_whitelist`` to ``domain_allowlist``.

.. code-block:: diff

     from django.core.validators import EmailValidator

    -EmailValidator(whitelist=["example.com"])
    +EmailValidator(allowlist=["example.com"])
    -EmailValidator(domain_whitelist=["example.org"])
    +EmailValidator(domain_allowlist=["example.org"])

``default_app_config``
~~~~~~~~~~~~~~~~~~~~~~

Removes module-level ``default_app_config`` assignments from ``__init__.py`` files:

.. code-block:: diff

    -default_app_config = 'my_app.apps.AppConfig'

Django 4.0
----------

`Release Notes <https://docs.djangoproject.com/en/4.0/releases/4.0/#features-deprecated-in-4-0>`__

There are no fixers for Django 4.0 at current.
Most of its deprecations don’t seem automatically fixable.

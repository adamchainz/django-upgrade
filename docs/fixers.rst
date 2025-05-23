======
Fixers
======

Fixers are the individual units that modify your files.
Some always run, but most run when the target version is set to a specific version or higher.

All versions
------------

The below fixers run regardless of the target version.

Versioned blocks
~~~~~~~~~~~~~~~~

**Name:** ``versioned_branches``

Removes outdated comparisons and blocks from ``if`` statements comparing to ``django.VERSION``.
Supports comparisons of the form:

.. code-block:: text

    if django.VERSION <comparator> (<X>, <Y>):
        ...

Where ``<comparator>`` is one of ``<``, ``<=`` , ``>``, or ``>=``, and ``<X>`` and ``<Y>`` are integer literals.
A single ``else`` block may be present, but ``elif`` is not supported.

.. code-block:: diff

    -if django.VERSION < (4, 1):
    -    class RenameIndex:
    -        ...

    -if django.VERSION >= (4, 1):
    -    constraint.validate()
    -else:
    -    custom_validation(constraint)
    +constraint.validate()

See also `pyupgrade’s similar feature <https://github.com/asottile/pyupgrade/#python2-and-old-python3x-blocks>`__ that removes outdated code from checks on the Python version.

.. _versioned_test_skip_decorators:

Versioned test skip decorators
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Name:** ``versioned_test_skip_decorators``

Removes outdated test skip decorators that compare to ``django.VERSION``.
Like the above, it requires comparisons of the form:

.. code-block:: text

    django.VERSION <comparator> (<X>, <Y>)

Supports these test skip decorators:

* |unittest.skipIf|__

  .. |unittest.skipIf| replace:: ``@unittest.skipIf``
  __ https://docs.python.org/3/library/unittest.html#unittest.skipIf

* |unittest.skipUnless|__

  .. |unittest.skipUnless| replace:: ``@unittest.skipUnless``
  __ https://docs.python.org/3/library/unittest.html#unittest.skipUnless

* |pytest.mark.skipif|__

  .. |pytest.mark.skipif| replace:: ``@pytest.mark.skipif``
  __ https://docs.pytest.org/en/stable/how-to/skipping.html#id1

For example:

.. code-block:: diff

     import unittest

     import django
     import pytest
     from django.test import TestCase

     class ExampleTests(TestCase):
    -    @unittest.skipIf(django.VERSION < (5, 1), "Django 5.1+")
         def test_one(self):
             ...

    -    @unittest.skipUnless(django.VERSION >= (5, 1), "Django 5.1+")
         def test_two(self):
             ...

    -    @pytest.mark.skipif(django.VERSION < (5, 1), reason="Django 5.1+")
         def test_three(self):
             ...

    -@unittest.skipIf(django.VERSION < (5, 1), "Django 5.1+")
     class Example2Tests(TestCase):
         ...

    -@pytest.mark.skipif(django.VERSION < (5, 1), reason="Django 5.1+")
     class Example3Tests(TestCase):
         ...

Django 5.2
----------

`Release Notes <https://docs.djangoproject.com/en/5.2/releases/5.2/>`__

.. _postgres_aggregate_order_by:

PostgreSQL aggregate ``order_by``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Name:** ``postgres_aggregate_order_by``

Rewrites calls to PostgreSQL aggregate functions using the old argument name ``ordering`` to the new name ``order_by``.

.. code-block:: diff

     from django.contrib.postgres.aggregates import ArrayAgg

    -Book.objects.aggregate(ArrayAgg("author", ordering="name"))
    +Book.objects.aggregate(ArrayAgg("author", order_by="name"))

.. _staticfiles_find_all:

staticfiles ``find()`` ``find_all``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Name:** ``staticfiles_find_all``

Rewrites calls to the staticfiles ``find()`` function using the old argument name ``all`` to the new name ``find_all``.

.. code-block:: diff

     from django.contrib.staticfiles import find

    -find("example.css", all=True)
    +find("example.css", find_all=True)

Django 5.1
----------

`Release Notes <https://docs.djangoproject.com/en/5.1/releases/5.1/>`__

.. _check_constraint_condition:

``CheckConstraint`` ``condition`` argument
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Name:** ``check_constraint_condition``

Rewrites calls to ``CheckConstraint`` and built-in subclasses from the old ``check`` argument to the new name ``condition``.

.. code-block:: diff

   -CheckConstraint(check=Q(amount__gte=0))
   +CheckConstraint(condition=Q(amount__gte=0))

Django 5.0
----------

`Release Notes <https://docs.djangoproject.com/en/5.0/releases/5.0/>`__

.. _model_field_choices:

Model field enumeration type ``.choices``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Name:** ``model_field_choices``

Drop ``.choices`` for model field ``choices`` parameters, where the value is a class defined in the same file.
This change is possible because the ``choices`` parameter now accepts enumeration types directly.

.. code-block:: diff

     from django.db import models

     class Suit(models.IntegerChoices):
         HEARTS = 1
         ...

     class Card(models.Model):
    -    suit = models.IntegerField(choices=Suit.choices, default=Suit.DEFAULT)
    +    suit = models.IntegerField(choices=Suit, default=Suit.DEFAULT)

``format_html()`` calls
~~~~~~~~~~~~~~~~~~~~~~~

**Name:** ``format_html``

Rewrites ``format_html()`` calls without ``args`` or ``kwargs`` but using ``str.format()``.
Such calls are most likely incorrectly applying formatting without escaping, making them vulnerable to HTML injection.
Such use cases are why calling ``format_html()`` without any arguments or keyword arguments was deprecated in `Ticket #34609 <https://code.djangoproject.com/ticket/34609>`__.

.. code-block:: diff

     from django.utils.html import format_html

    -format_html("<marquee>{}</marquee>".format(message))
    +format_html("<marquee>{}</marquee>", message)

    -format_html("<marquee>{name}</marquee>".format(name=name))
    +format_html("<marquee>{name}</marquee>", name=name)

Django 4.2
----------

`Release Notes <https://docs.djangoproject.com/en/4.2/releases/4.2/>`__

``STORAGES`` setting
~~~~~~~~~~~~~~~~~~~~

**Name:** ``settings_storages``

Combines deprecated settings ``DEFAULT_FILE_STORAGE`` and ``STATICFILES_STORAGE`` into the new ``STORAGES`` setting, within settings files.
Only applies if all old settings are defined as strings, at module level, and a ``STORAGES`` setting hasn’t been defined.

Settings files are heuristically detected as modules with the whole word “settings” somewhere in their path.
For example ``myproject/settings.py`` or ``myproject/settings/production.py``.

.. code-block:: diff

    -DEFAULT_FILE_STORAGE = "example.storages.ExtendedFileSystemStorage"
    -STATICFILES_STORAGE = "example.storages.ExtendedS3Storage"
    +STORAGES = {
    +    "default": {
    +        "BACKEND": "example.storages.ExtendedFileSystemStorage",
    +    },
    +    "staticfiles": {
    +        "BACKEND": "example.storages.ExtendedS3Storage",
    +    },
    +}

If the module has a ``from ... import *`` with a module path mentioning “settings”, django-upgrade makes an educated guess that a base ``STORAGES`` setting is imported from there.
It then uses ``**`` to extend that with any values in the current module:

.. code-block:: diff

     from example.settings.base import *
    -DEFAULT_FILE_STORAGE = "example.storages.S3Storage"
    +STORAGES = {
    +    **STORAGES,
    +    "default": {
    +        "BACKEND": "example.storages.S3Storage",
    +    },
    +}

Test client HTTP headers
~~~~~~~~~~~~~~~~~~~~~~~~

**Name:** ``test_http_headers``

Transforms HTTP headers from the old WSGI kwarg format to use the new ``headers`` dictionary, for:

* ``Client`` method like ``self.client.get()``
* ``Client`` instantiation
* ``RequestFactory`` instantiation

.. code-block:: diff

    -response = self.client.get("/", HTTP_ACCEPT="text/plain")
    +response = self.client.get("/", headers={"accept": "text/plain"})

     from django.test import Client
    -Client(HTTP_ACCEPT_LANGUAGE="fr-fr")
    +Client(headers={"accept-language": "fr-fr"})

     from django.test import RequestFactory
    -RequestFactory(HTTP_USER_AGENT="curl")
    +RequestFactory(headers={"user-agent": "curl"})

.. _index_together:

``index_together`` deprecation
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Name:** ``index_together``

Rewrites ``index_together`` declarations into ``indexes`` declarations in model ``Meta`` classes.

.. code-block:: diff

     from django.db import models

     class Duck(models.Model):
         class Meta:
    -       index_together = [["bill", "tail"]]
    +       indexes = [models.Index(fields=["bill", "tail"])]

``assertFormsetError`` and ``assertQuerysetEqual``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Name:** ``assert_set_methods``

Rewrites calls to these test case methods from the old names to the new ones with capitalized “Set”.

.. code-block:: diff

    -self.assertFormsetError(response.context["form"], "username", ["Too long"])
    +self.assertFormSetError(response.context["form"], "username", ["Too long"])

    -self.assertQuerysetEqual(authors, ["Brad Dayley"], lambda a: a.name)
    +self.assertQuerySetEqual(authors, ["Brad Dayley"], lambda a: a.name)

Django 4.1
----------

`Release Notes <https://docs.djangoproject.com/en/4.1/releases/4.1/>`__

``django.utils.timezone.utc`` deprecations
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Name:** ``utils_timezone``

Rewrites imports of ``django.utils.timezone.utc`` to use ``datetime.timezone.utc``.
Requires an existing import of the ``datetime`` module.

.. code-block:: diff

     import datetime
    -from django.utils.timezone import utc

    -calculate_some_datetime(utc)
    +calculate_some_datetime(datetime.timezone.utc)

.. code-block:: diff

     import datetime as dt
     from django.utils import timezone


    -do_a_thing(timezone.utc)
    +do_a_thing(dt.timezone.utc)

``assertFormError()`` and ``assertFormsetError()``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Name:** ``assert_form_error``

Rewrites calls to these test case methods from the old signatures to the new ones.

.. code-block:: diff

    -self.assertFormError(response, "form", "username", ["Too long"])
    +self.assertFormError(response.context["form"], "username", ["Too long"])

    -self.assertFormError(response, "form", "username", None)
    +self.assertFormError(response.context["form"], "username", [])

    -self.assertFormsetError(response, "formset", 0, "username", ["Too long"])
    +self.assertFormsetError(response.context["formset"], 0, "username", ["Too long"])

    -self.assertFormsetError(response, "formset", 0, "username", None)
    +self.assertFormsetError(response.context["formset"], 0, "username", [])

Django 4.0
----------

`Release Notes <https://docs.djangoproject.com/en/4.0/releases/4.0/>`__

``USE_L10N``
~~~~~~~~~~~~

**Name:** ``use_l10n``

Removes the deprecated ``USE_L10N`` setting if set to its default value of ``True``.

Settings files are heuristically detected as modules with the whole word “settings” somewhere in their path.
For example ``myproject/settings.py`` or ``myproject/settings/production.py``.
Settings assignments may be module-level or class-level.

.. code-block:: diff

    -USE_L10N = True

     class BaseSettings:
    -    USE_L10N = True

``lookup_needs_distinct``
~~~~~~~~~~~~~~~~~~~~~~~~~

**Name:** ``admin_lookup_needs_distinct``

Renames the undocumented ``django.contrib.admin.utils.lookup_needs_distinct`` to ``lookup_spawns_duplicates``:

.. code-block:: diff

    -from django.contrib.admin.utils import lookup_needs_distinct
    +from django.contrib.admin.utils import lookup_spawns_duplicates

    -if lookup_needs_distinct(self.opts, search_spec):
    +if lookup_spawns_duplicates(self.opts, search_spec):
        ...

Compatibility imports
~~~~~~~~~~~~~~~~~~~~~

Rewrites some compatibility imports:

* ``django.utils.translation.template.TRANSLATOR_COMMENT_MARK`` in ``django.template.base``

.. code-block:: diff

    -from django.template.base import TRANSLATOR_COMMENT_MARK
    +from django.utils.translation.template import TRANSLATOR_COMMENT_MARK

Django 3.2
----------

`Release Notes <https://docs.djangoproject.com/en/3.2/releases/3.2/>`__

``@admin.action()``
~~~~~~~~~~~~~~~~~~~

**Name:** ``admin_decorators``

Rewrites functions that have admin action attributes assigned to them to use the new |@admin.action decorator|_.
This only applies in files that use ``from django.contrib import admin`` or ``from django.contrib.gis import admin``.

.. |@admin.action decorator| replace:: ``@admin.action()`` decorator
.. _@admin.action decorator: https://docs.djangoproject.com/en/stable/ref/contrib/admin/actions/#django.contrib.admin.action

.. code-block:: diff

     from django.contrib import admin

     # Module-level actions:

    +@admin.action(
    +    description="Publish articles",
    +)
     def make_published(modeladmin, request, queryset):
         ...

    -make_published.short_description = "Publish articles"

     # …and within classes:

     @admin.register(Book)
     class BookAdmin(admin.ModelAdmin):
    +    @admin.action(
    +        description="Unpublish articles",
    +        permissions=("unpublish",),
    +    )
         def make_unpublished(self, request, queryset):
             ...

    -    make_unpublished.allowed_permissions = ("unpublish",)
    -    make_unpublished.short_description = "Unpublish articles"

``@admin.display()``
~~~~~~~~~~~~~~~~~~~~

**Name:** ``admin_decorators``

Rewrites functions that have admin display attributes assigned to them to use the new |@admin.display decorator|_.
This only applies in files that use ``from django.contrib import admin`` or ``from django.contrib.gis import admin``.

.. |@admin.display decorator| replace:: ``@admin.display()`` decorator
.. _@admin.display decorator: https://docs.djangoproject.com/en/stable/ref/contrib/admin/#django.contrib.admin.display

.. code-block:: diff

     from django.contrib import admin

     # Module-level display functions:

    +@admin.display(
    +    description="NAME",
    +)
     def upper_case_name(obj):
         ...

    -upper_case_name.short_description = "NAME"

     # …and within classes:

     @admin.register(Book)
     class BookAdmin(admin.ModelAdmin):
    +    @admin.display(
    +        description='Is Published?',
    +        boolean=True,
    +        ordering='-publish_date',
    +    )
         def is_published(self, obj):
             ...

    -    is_published.boolean = True
    -    is_published.admin_order_field = '-publish_date'
    -    is_published.short_description = 'Is Published?'

``BaseCommand.requires_system_checks``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Name:** ``management_commands``

Rewrites the ``requires_system_checks`` attributes of management command classes from bools to ``"__all__"`` or ``[]`` as appropriate.
This only applies in command files, which are heuristically detected as files with ``management/commands`` somewhere in their path.

.. code-block:: diff

     from django.core.management.base import BaseCommand

     class Command(BaseCommand):
    -    requires_system_checks = True
    +    requires_system_checks = "__all__"

     class SecondCommand(BaseCommand):
    -    requires_system_checks = False
    +    requires_system_checks = []

``EmailValidator``
~~~~~~~~~~~~~~~~~~

**Name:** ``email_validator``

Rewrites the ``whitelist`` keyword argument to its new name ``allowlist``.

.. code-block:: diff

     from django.core.validators import EmailValidator

    -EmailValidator(whitelist=["example.com"])
    +EmailValidator(allowlist=["example.com"])

``default_app_config``
~~~~~~~~~~~~~~~~~~~~~~

**Name:** ``default_app_config``

Removes module-level ``default_app_config`` assignments from ``__init__.py`` files:

.. code-block:: diff

    -default_app_config = 'my_app.apps.AppConfig'

Django 3.1
----------

`Release Notes <https://docs.djangoproject.com/en/3.1/releases/3.1/>`__

``JSONField``
~~~~~~~~~~~~~

**Name:** ``compatibility_imports``

Rewrites imports of ``JSONField`` and related transform classes from those in ``django.contrib.postgres`` to the new all-database versions.
Ignores usage in migration files, since Django kept the old class around to support old migrations.
You will need to make migrations after this fix makes changes to models.

.. code-block:: diff

    -from django.contrib.postgres.fields import JSONField
    +from django.db.models import JSONField

``PASSWORD_RESET_TIMEOUT_DAYS``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Name:** ``password_reset_timeout_days``

Rewrites the setting ``PASSWORD_RESET_TIMEOUT_DAYS`` to ``PASSWORD_RESET_TIMEOUT``, adding the multiplication by the number of seconds in a day.

Settings files are heuristically detected as modules with the whole word “settings” somewhere in their path.
For example ``myproject/settings.py`` or ``myproject/settings/production.py``.

.. code-block:: diff

    -PASSWORD_RESET_TIMEOUT_DAYS = 4
    +PASSWORD_RESET_TIMEOUT = 60 * 60 * 24 * 4

``Signal``
~~~~~~~~~~

**Name:** ``signal_providing_args``

Removes the deprecated documentation-only ``providing_args`` argument.

.. code-block:: diff

     from django.dispatch import Signal
    -my_cool_signal = Signal(providing_args=["documented", "arg"])
    +my_cool_signal = Signal()

``get_random_string``
~~~~~~~~~~~~~~~~~~~~~

**Name:** ``crypto_get_random_string``

Injects the now-required ``length`` argument, with its previous default ``12``.

.. code-block:: diff

     from django.utils.crypto import get_random_string
    -key = get_random_string(allowed_chars="01234567899abcdef")
    +key = get_random_string(length=12, allowed_chars="01234567899abcdef")

.. _null_boolean_field:

``NullBooleanField``
~~~~~~~~~~~~~~~~~~~~

**Name:** ``null_boolean_field``

Transforms the ``NullBooleanField()`` model field to ``BooleanField(null=True)``.
Applied only in model files, not migration files, since Django kept the old class around to support old migrations.
You will need to make migrations after this fix makes changes to models.

.. code-block:: diff

    -from django.db.models import Model, NullBooleanField
    +from django.db.models import Model, BooleanField

     class Book(Model):
    -    valuable = NullBooleanField("Valuable")
    +    valuable = BooleanField("Valuable", null=True)

``ModelMultipleChoiceField``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Name:** ``forms_model_multiple_choice_field``

Replace ``list`` error message key with ``list_invalid`` on forms ``ModelMultipleChoiceField``.

.. code-block:: diff

    -forms.ModelMultipleChoiceField(error_messages={"list": "Enter multiple values."})
    +forms.ModelMultipleChoiceField(error_messages={"invalid_list": "Enter multiple values."})

Django 3.0
----------

`Release Notes <https://docs.djangoproject.com/en/3.0/releases/3.0/>`__

``django.utils.encoding`` aliases
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Name:** ``utils_encoding``

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

**Name:** ``utils_http``:

Rewrites the ``urlquote()``, ``urlquote_plus()``, ``urlunquote()``, and ``urlunquote_plus()`` functions to the ``urllib.parse`` versions.
Also rewrites the internal function ``is_safe_url()`` to ``url_has_allowed_host_and_scheme()``.

.. code-block:: diff

    -from django.utils.http import urlquote
    +from urllib.parse import quote

    -escaped_query_string = urlquote(query_string)
    +escaped_query_string = quote(query_string)

``django.utils.text`` deprecation
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Name:** ``utils_text``

Rewrites ``unescape_entities()`` with the standard library ``html.escape()``.

.. code-block:: diff

    -from django.utils.text import unescape_entities
    +import html

    -unescape_entities("some input string")
    +html.escape("some input string")

``django.utils.translation`` deprecations
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Name:** ``utils_translation``

Rewrites the ``ugettext()``, ``ugettext_lazy()``, ``ugettext_noop()``, ``ungettext()``, and ``ungettext_lazy()`` functions to their non-u-prefixed versions.

.. code-block:: diff

    -from django.utils.translation import ugettext as _, ungettext
    +from django.utils.translation import gettext as _, ngettext

    -ungettext("octopus", "octopodes", n)
    +ngettext("octopus", "octopodes", n)

Django 2.2
----------

`Release Notes <https://docs.djangoproject.com/en/2.2/releases/2.2/>`__

``HttpRequest.headers``
~~~~~~~~~~~~~~~~~~~~~~~

**Name:** ``request_headers``

Rewrites use of ``request.META`` to read HTTP headers to instead use |request.headers|_.
Header lookups are done in lowercase per `the HTTP/2 specification <https://httpwg.org/specs/rfc9113.html#HttpHeaders>`__.

.. |request.headers| replace:: ``request.headers``
.. _request.headers: https://docs.djangoproject.com/en/stable/ref/request-response/#django.http.HttpRequest.headers

.. code-block:: diff

    -request.META['HTTP_ACCEPT_ENCODING']
    +request.headers['accept-encoding']

    -self.request.META.get('HTTP_SERVER', '')
    +self.request.headers.get('server', '')

    -request.META.get('CONTENT_LENGTH')
    +request.headers.get('content-length')

    -"HTTP_SERVER" in request.META
    +"server" in request.headers

``QuerySetPaginator``
~~~~~~~~~~~~~~~~~~~~~

**Name:** ``queryset_paginator``

Rewrites deprecated alias ``django.core.paginator.QuerySetPaginator`` to ``Paginator``.

.. code-block:: diff

    -from django.core.paginator import QuerySetPaginator
    +from django.core.paginator import Paginator

    -QuerySetPaginator(...)
    +Paginator(...)


``FixedOffset``
~~~~~~~~~~~~~~~

**Name:** ``timezone_fixedoffset``

Rewrites deprecated class ``FixedOffset(x, y))`` to ``timezone(timedelta(minutes=x), y)``

Known limitation: this fixer will leave code broken with an ``ImportError`` if ``FixedOffset`` is called with only ``*args`` or ``**kwargs``.

.. code-block:: diff

    -from django.utils.timezone import FixedOffset
    -FixedOffset(120, "Super time")
    +from datetime import timedelta, timezone
    +timezone(timedelta(minutes=120), "Super time")

``FloatRangeField``
~~~~~~~~~~~~~~~~~~~

**Name:** ``postgres_float_range_field``

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

**Name:** ``testcase_databases``

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

Django 2.1
----------

`Release Notes <https://docs.djangoproject.com/en/2.1/releases/2.1/>`__

No fixers yet.

Django 2.0
----------

`Release Notes <https://docs.djangoproject.com/en/2.0/releases/2.0/>`__

.. _django_urls:

URLs
~~~~

**Name:** ``django_urls``

Rewrites imports of ``include()`` and ``url()`` from ``django.conf.urls`` to ``django.urls``.
``url()`` calls using compatible regexes are rewritten to the |new path() syntax|_, otherwise they are converted to call ``re_path()``.

.. |new path() syntax| replace:: new ``path()`` syntax
.. _new path() syntax: https://docs.djangoproject.com/en/2.0/releases/2.0/#simplified-url-routing-syntax

.. code-block:: diff

    -from django.conf.urls import include, url
    +from django.urls import include, path, re_path

     urlpatterns = [
    -    url(r'^$', views.index, name='index'),
    +    path('', views.index, name='index'),
    -    url(r'^about/$', views.about, name='about'),
    +    path('about/', views.about, name='about'),
    -    url(r'^post/(?P<slug>[-a-zA-Z0-9_]+)/$', views.post, name='post'),
    +    path('post/<slug:slug>/', views.post, name='post'),
    -    url(r'^weblog', include('blog.urls')),
    +    re_path(r'^weblog', include('blog.urls')),
     ]

Existing ``re_path()`` calls are also rewritten to the ``path()`` syntax when eligible.

.. code-block:: diff

    -from django.urls import include, re_path
    +from django.urls import include, path, re_path

     urlpatterns = [
    -    re_path(r'^about/$', views.about, name='about'),
    +    path('about/', views.about, name='about'),
         re_path(r'^post/(?P<slug>[\w-]+)/$', views.post, name='post'),
     ]

The compatible regexes that will be converted to use `path converters <https://docs.djangoproject.com/en/stable/topics/http/urls/#path-converters>`__ are the following:

* ``[^/]+`` → ``str``
* ``[0-9]+`` → ``int``
* ``[-a-zA-Z0-9_]+`` → ``slug``
* ``[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}`` → ``uuid``
* ``.+`` → ``path``

These are taken from the path converter classes.

For some cases, this change alters the type of the arguments passed to the view, from ``str`` to the converted type (e.g. ``int``).
This is not guaranteed backwards compatible: there is a chance that the view expects a string, rather than the converted type.
But, pragmatically, it seems 99.9% of views do not require strings, and instead work with either strings or the converted type.
Thus, you should test affected paths after this fixer makes any changes.

Note that ``[\w-]`` is sometimes used for slugs, but is not converted because it might be incompatible.
That pattern matches all Unicode word characters, such as “α”, unlike Django's ``slug`` converter, which only matches Latin characters.

Compatibility imports
~~~~~~~~~~~~~~~~~~~~~

**Name:** ``compatibility_imports``

Rewrites some compatibility imports:

* ``lru_cache`` from ``django.utils.functional`` to use ``functools``.
* ``ContextDecorator`` from ``django.utils.decorators`` to use ``contextlib``
* ``SimpleCookie`` from ``django.http.cookie`` to use ``http.cookies``

.. code-block:: diff

    -from django.utils.functional import lru_cache
    +from functools import lru_cache

    -from django.utils.decorators import ContextDecorator
    +from contextlib import ContextDecorator

    -from django.http.cookie import SimpleCookie
    +from http.cookies import SimpleCookie

``<func>.allow_tags = True``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Name:** ``admin_allow_tags``

Removes assignments of ``allow_tags`` attributes to ``True``.
This was an admin feature to allow display functions to return HTML without marking it as unsafe,  deprecated in Django 1.9.
In practice, most display functions that return HTML already use |format_html()|_ or similar, so the attribute wasn’t necessary.
This only applies in files that use ``from django.contrib import admin`` or ``from django.contrib.gis import admin``.

.. |format_html()| replace:: ``format_html()``
.. _format_html(): https://docs.djangoproject.com/en/stable/ref/utils/#django.utils.html.format_html

.. code-block:: diff

    from django.contrib import admin

    def upper_case_name(obj):
        ...

   -upper_case_name.allow_tags = True

Django 1.11
-----------

`Release Notes <https://docs.djangoproject.com/en/1.11/releases/1.11/>`__

Compatibility imports
~~~~~~~~~~~~~~~~~~~~~

**Name:** ``compatibility_imports``

Rewrites some compatibility imports:

* ``django.core.exceptions.EmptyResultSet`` in ``django.db.models.query``, ``django.db.models.sql``, and ``django.db.models.sql.datastructures``
* ``django.core.exceptions.FieldDoesNotExist`` in ``django.db.models.fields``

Whilst mentioned in the `Django 3.1 release notes <https://docs.djangoproject.com/en/3.1/releases/3.1/#id1>`_, these have been possible since Django 1.11.

.. code-block:: diff

    -from django.db.models.query import EmptyResultSet
    +from django.core.exceptions import EmptyResultSet

    -from django.db.models.fields import FieldDoesNotExist
    +from django.core.exceptions import FieldDoesNotExist

Django 1.10
-----------

`Release Notes <https://docs.djangoproject.com/en/1.10/releases/1.10/>`__

``request.user`` boolean attributes
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Name:** ``request_user_attributes``

Rewrites calls to ``request.user.is_authenticated()`` and ``request.user.is_anonymous()`` to remove the parentheses, per `the deprecation <https://docs.djangoproject.com/en/1.10/releases/1.10/#using-user-is-authenticated-and-user-is-anonymous-as-methods>`__.

.. code-block:: diff

    -request.user.is_authenticated()
    +request.user.is_authenticated

    -self.request.user.is_anonymous()
    +self.request.user.is_anonymous

Compatibility imports
~~~~~~~~~~~~~~~~~~~~~

Rewrites some compatibility imports:

* ``django.templatetags.static.static`` in ``django.contrib.staticfiles.templatetags.staticfiles``

   (Whilst mentioned in the `Django 2.1 release notes <https://docs.djangoproject.com/en/2.1/releases/2.1/#features-deprecated-in-2-1>`_, this has been possible since Django 1.10.)

* ``django.urls.*`` in ``django.core.urlresolvers.*``

.. code-block:: diff

    -from django.contrib.staticfiles.templatetags.staticfiles import static
    +from django.templatetags.static import static

    -from django.core.urlresolvers import reverse
    +from django.urls import reverse

    -from django.core.urlresolvers import resolve
    +from django.urls import resolve

Django 1.9
-----------

`Release Notes <https://docs.djangoproject.com/en/stable/releases/1.9/>`__

``on_delete`` argument
~~~~~~~~~~~~~~~~~~~~~~

**Name:** ``on_delete``

Add ``on_delete=models.CASCADE`` to ``ForeignKey`` and ``OneToOneField``:

.. code-block:: diff

     from django.db import models

    -models.ForeignKey("auth.User")
    +models.ForeignKey("auth.User", on_delete=models.CASCADE)

    -models.OneToOneField("auth.User")
    +models.OneToOneField("auth.User", on_delete=models.CASCADE)

This fixer also support from-imports:

.. code-block:: diff

    -from django.db.models import ForeignKey
    +from django.db.models import CASCADE, ForeignKey

    -ForeignKey("auth.User")
    +ForeignKey("auth.User", on_delete=CASCADE)

``DATABASES``
~~~~~~~~~~~~~

**Name:** ``settings_database_postgresql``

Update the ``DATABASES`` setting backend path ``django.db.backends.postgresql_psycopg2`` to use the renamed version ``django.db.backends.postgresql``.

Settings files are heuristically detected as modules with the whole word “settings” somewhere in their path.
For example ``myproject/settings.py`` or ``myproject/settings/production.py``.

.. code-block:: diff

    DATABASES = {
        "default": {
   -        "ENGINE": "django.db.backends.postgresql_psycopg2",
   +        "ENGINE": "django.db.backends.postgresql",
            "NAME": "mydatabase",
            "USER": "mydatabaseuser",
            "PASSWORD": "mypassword",
            "HOST": "127.0.0.1",
            "PORT": "5432",
        }
    }

Compatibility imports
~~~~~~~~~~~~~~~~~~~~~

**Name:** ``compatibility_imports``

Rewrites some compatibility imports:

* ``django.forms.utils.pretty_name`` in ``django.forms.forms``
* ``django.forms.boundfield.BoundField`` in ``django.forms.forms``
* ``django.forms.widgets.SelectDateWidget`` in ``django.forms.extras``

Whilst mentioned in the `Django 3.1 release notes <https://docs.djangoproject.com/en/3.1/releases/3.1/#id1>`_, these have been possible since Django 1.9.

.. code-block:: diff

    -from django.forms.forms import pretty_name
    +from django.forms.utils import pretty_name

Django 1.8
----------

`Release Notes <https://docs.djangoproject.com/en/stable/releases/1.8/>`__

No fixers yet.

Django 1.7
----------

`Release Notes <https://docs.djangoproject.com/en/stable/releases/1.7/>`__

Admin model registration
~~~~~~~~~~~~~~~~~~~~~~~~

**Name:** ``admin_register``

Rewrites ``admin.site.register()`` calls to the new |@admin.register|_ decorator syntax when eligible.
This only applies in files that use ``from django.contrib import admin`` or ``from django.contrib.gis import admin``.

.. |@admin.register| replace:: ``@admin.register()``
.. _@admin.register: https://docs.djangoproject.com/en/stable/ref/contrib/admin/#the-register-decorator

.. code-block:: diff

     from django.contrib import admin

    +@admin.register(MyModel1, MyModel2)
     class MyCustomAdmin(admin.ModelAdmin):
         ...

    -admin.site.register(MyModel1, MyCustomAdmin)
    -admin.site.register(MyModel2, MyCustomAdmin)

This also works with custom admin sites.
Such calls are detected heuristically based on three criteria:

1. The object whose ``register()`` method is called has a name ending with ``site``.
2. The registered class has a name ending with ``Admin``.
3. The filename has the word ``admin`` somewhere in its path.

.. code-block:: diff

    from myapp.admin import custom_site
    from django.contrib import admin

    +@admin.register(MyModel)
    +@admin.register(MyModel, site=custom_site)
    class MyModelAdmin(admin.ModelAdmin):
        pass

    -custom_site.register(MyModel, MyModelAdmin)
    -admin.site.register(MyModel, MyModelAdmin)

If a ``register()`` call is preceded by an ``unregister()`` call that includes the same model, it is ignored.

.. code-block:: python

    from django.contrib import admin


    class MyCustomAdmin(admin.ModelAdmin): ...


    admin.site.unregister(MyModel1)
    admin.site.register(MyModel1, MyCustomAdmin)

Compatibility imports
~~~~~~~~~~~~~~~~~~~~~

Rewrites some compatibility imports:

* ``django.contrib.admin.helpers.ACTION_CHECKBOX_NAME`` in ``django.contrib.admin``
* ``django.template.context.BaseContext``, ``django.template.context.Context``, ``django.template.context.ContextPopException`` and ``django.template.context.RequestContext`` in ``django.template.base``

.. code-block:: diff

    -from django.contrib.admin import ACTION_CHECKBOX_NAME
    +from django.contrib.admin.helpers import ACTION_CHECKBOX_NAME

    -from django.template.base import Context
    +from django.template.context import Context

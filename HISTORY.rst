=======
History
=======

* Add Django 2.0+ fixer to rewrite imports of ``lru_cache`` from ``django.utils.functional`` to use ``functools``.

1.3.2 (2021-09-23)
------------------

* Avoid rewriting ``request.META`` to ``request.headers`` in assignments.
  This pattern is used in tests, and works for ``request.META`` but not ``request.headers``.

  Thanks to Bruno Alla for the report in `Issue #74 <https://github.com/adamchainz/django-upgrade/issues/74>`__.

1.3.1 (2021-09-22)
------------------

* Fix import fixers to not crash on star imports (``from foo import *``).

  Thanks to Mikhail for the report in `Issue #70 <https://github.com/adamchainz/django-upgrade/issues/70>`__.

1.3.0 (2021-09-22)
------------------

* Fix ``get_random_string()`` fixer to not add the argument to calls like ``crypto.get_random_string(12)``.

* Add fixers to remove various compatibility imports removed in Django 3.1.

  Thanks to Bruno Alla in `PR #44 <https://github.com/adamchainz/django-upgrade/pull/44>`__.

* Add fixer for Django 2.2 to rewrite ``request.META`` access of headers to ``HttpRequest.headers``.

* Add fixer for Django 2.0 to rewrite ``include()`` and ``url()`` from ``django.conf.urls`` to ``django.urls``.
  ``url()`` may be rewritten to ``path()`` or ``re_path()`` accordingly.

  Thanks to Bruno Alla for the original implementation of regex-to-path conversion in django-codemod.
  Thanks to Matthias Kestenholz for an initial PR.

* Add fixer for Django 1.9 requirement to pass ``on_delete`` to ``ForeignKey`` and ``OneToOneField``.

  Thanks to Bruno Alla in `PR #61 <https://github.com/adamchainz/django-upgrade/pull/61>`__.

1.2.0 (2021-09-02)
------------------

* Support Python 3.10.

* Support single level module imports of names too, such as using o
  ``from django.utils import crypto`` with ``crypto.get_random_string()``.

* Add fixer for Django 3.1 deprecation of ``NullBooleanField``.

* Add fixers for Django 3.0 deprecation of functions in ``django.utils.http``, ``django.utils.text``, and ``django.utils.translation``.

* Add fixer for Django 2.2 rename of ``FloatRangeField`` to ``DecimalRangeField``.

* Add fixer for Django 2.2 deprecation of test case attributes ``allow_database_queries`` and ``multi_db``.

* Fix inserted imports to match indentation of the point they are inserted.

1.1.0 (2021-08-28)
------------------

* Add fixer for Django 3.1 ``JSONField`` moves.

* Add fixer for Django 3.1 removal of ``Signal``\’s argument ``providing_args``.

* Add fixer for Django 3.1 requirement to pass ``get_random_string()`` the ``length`` argument.

* Fix Python 3.8 compatibility.

* Drop Python 3.6 and 3.7 support, since they never worked, and the incompatibilities in the ``ast`` module are hard to cover.

1.0.0 (2021-08-27)
------------------

* Initial release.

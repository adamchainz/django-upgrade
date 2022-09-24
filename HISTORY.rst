=======
History
=======

* Add Django 1.7+ fixer to rewrite ``admin.site.register()`` calls into ``@admin.register()`` when eligible.

  Thanks to Thibaut Decombe in `PR #189 <https://github.com/adamchainz/django-upgrade/pull/189>`__.

* Add Django 3.2+ fixer to rewrite admin action function attributes to use the ``@admin.action()`` decorator.

* Add Django 3.2+ fixer to rewrite admin display function attributes to use the ``@admin.display()`` decorator.

* Add Django 4.1+ fixer to rewrite calls to test case methods ``assertFormError()`` and ``assertFormsetError()`` from their old signatures to the new ones.

* Add Django 2.0+ fixer to drop assignments of ``allow_tags`` attributes to ``True``.

* Make ``request.headers`` fixer also rewrite accesses of the ``Content-Length`` and ``Content-Type`` headers.

  Thanks to Christian Bundy in `PR #226 <https://github.com/adamchainz/django-upgrade/pull/226>`__.

* Make ``on_delete`` fixer also support ``ForeignKey`` and ``OneToOneField`` imported from ``django.db.models``.

  Thanks to Thibaut Decombe in `PR #236 <https://github.com/adamchainz/django-upgrade/pull/236>`__.

* Make ``NullBooleanField`` fixer preserve existing ``null`` arguments.

  Thanks to Joseph Zammit in `Issue #245 <https://github.com/adamchainz/django-upgrade/issues/245>`__.

* Make fixers that erase lines also erase any trailing comments.

* Fix leaving a trailing comma when editing imports in certain cases.

* Expand the range of files considered settings files.

* Require at least one filename.

  Thanks to Daan Vielen in `Issue #238 <https://github.com/adamchainz/django-upgrade/issues/238>`__.

* Update README with info on how to run an upgrade on entire project.

  Thanks to Daan Vielen in `Issue #240 <https://github.com/adamchainz/django-upgrade/issues/240>`__.

1.10.0 (2022-09-07)
-------------------

* Add Django 3.2+ fixer to update ``requires_system_checks`` in management command classes.

  Thanks to Bruno Alla in `PR #184 <https://github.com/adamchainz/django-upgrade/pull/184>`__.

1.9.0 (2022-08-25)
------------------

* Add Django 4.0+ fixer to remove ``USE_L10N = True`` setting.

  Thanks to Johnny Metz in `PR #173 <https://github.com/adamchainz/django-upgrade/pull/173>`__.

* Add fixer to remove outdated blocks based on comparing ``django.VERSION`` to old versions:

  .. code-block:: diff

      -if django.VERSION > (4, 1):
      -    constraint.validate()
      +constraint.validate()

* Update Django 2.0+ URL fixer to rewrite ``re_path()`` calls into ``path()`` when eligible.

  Thanks to Thibaut Decombe in `PR #167 <https://github.com/adamchainz/django-upgrade/pull/167>`__.

1.8.1 (2022-08-25)
------------------

* Fix ``timezone.utc`` fixer to import and use ``timezone.utc`` correctly.

  Thanks to Víðir Valberg Guðmundsson for the report in `Issue #172 <https://github.com/adamchainz/django-upgrade/issues/172>`__.

1.8.0 (2022-08-11)
------------------

* Support Django 4.1 as a target version.

* Add Django 4.1+ fixer to rewrite imports of ``utc`` from ``django.utils.timezone`` to use
  ``datetime.timezone``.

  Thanks to Hasan Ramezani in `PR #169 <https://github.com/adamchainz/django-upgrade/pull/169>`__.

1.7.0 (2022-05-11)
------------------

* Support Python 3.11.

1.6.1 (2022-05-04)
------------------

* Fix ``default_app_config`` fixer to work with ``__init__.py`` files in subdirectories.

  Thanks to Bruno Alla in `PR #144 <https://github.com/adamchainz/django-upgrade/pull/144>`__.

* Add ``--version`` flag.

  Thanks to Ferran Jovell in `PR #143 <https://github.com/adamchainz/django-upgrade/pull/143>`__.

1.6.0 (2022-05-04)
------------------

* Add Django 3.2+ fixer to remove ``default_app_config`` assignments in ``__init__.py`` files.

  Thanks to Bruno Alla in `PR #140 <https://github.com/adamchainz/django-upgrade/pull/140>`__.

1.5.0 (2022-04-14)
------------------

* Fix URL rewriting to avoid converting regular expressions that don’t end with ``$``.
  If the ``$`` is missing, Django will search for the given regular expression anywhere in the path.

  Thanks to qdufrois for the report in `Issue #121 <https://github.com/adamchainz/django-upgrade/issues/121>`__.

* Made ``JSONField`` and ``NullBooleanField`` fixers ignore migrations files.
  Django kept these old field classes around for use in historical migrations, so there’s no need to rewrite such cases.

  Thanks to Matthieu Rigal and Bruno Alla for the report in `Issue #79 <https://github.com/adamchainz/django-upgrade/issues/79>`__.

1.4.0 (2021-10-23)
------------------

* Add Django 2.0+ fixer to rewrite imports of ``lru_cache`` from ``django.utils.functional`` to use ``functools``.

* Support Django 4.0 as a target version.
  There are no fixers for it at current.
  Most of its deprecations don’t seem automatically fixable.

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

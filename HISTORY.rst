=======
History
=======

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

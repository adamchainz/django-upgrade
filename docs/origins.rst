=======
Origins
=======

`django-codemod <https://django-codemod.readthedocs.io/en/latest/>`__ was an existing Django auto-upgrade tool, written by Bruno Alla.
Unfortunately its underlying library `LibCST <https://pypi.org/project/libcst/>`__ is (or at least was) particularly slow, making it annoying to run django-codemod on every commit and in CI.

django-upgrade started as an experiment in reimplementing such a tool using the same techniques as the fantastic `pyupgrade <https://github.com/asottile/pyupgrade>`__.
The tool leans on the standard library’s `ast <https://docs.python.org/3/library/ast.html>`__ and `tokenize <https://docs.python.org/3/library/tokenize.html>`__ modules, the latter via the `tokenize-rt wrapper <https://github.com/asottile/tokenize-rt>`__.
This means it will always be fast and support the latest versions of Python.

In a quick benchmark against a medium Django repository, with 153k lines of Python:

* django-codemod took 133 seconds
* django-upgrade took 0.5 seconds

Since its creation, django-upgrade has seen great adoption.

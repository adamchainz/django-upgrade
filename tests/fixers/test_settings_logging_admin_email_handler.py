from __future__ import annotations

from functools import partial

from django_upgrade.data import Settings
from tests.fixers import tools

settings = Settings(target_version=(6, 1))
check_noop = partial(tools.check_noop, settings=settings)
check_transformed = partial(tools.check_transformed, settings=settings)


def test_not_settings_file():
    check_noop(
        """\
        LOGGING = {
            "handlers": {
                "mail_admins": {
                    "class": "django.utils.log.AdminEmailHandler",
                    "email_backend": "myapp.backends.EmailBackend",
                },
            },
        }
        """,
    )


def test_old_version():
    check_noop(
        """\
        LOGGING = {
            "handlers": {
                "mail_admins": {
                    "class": "django.utils.log.AdminEmailHandler",
                    "email_backend": "myapp.backends.EmailBackend",
                },
            },
        }
        """,
        settings=Settings(target_version=(6, 0)),
        filename="settings.py",
    )


def test_two_targets():
    check_noop(
        """\
        LOGGING = OTHER = {
            "handlers": {
                "mail_admins": {
                    "class": "django.utils.log.AdminEmailHandler",
                    "email_backend": "myapp.backends.EmailBackend",
                },
            },
        }
        """,
        filename="settings.py",
    )


def test_not_logging():
    check_noop(
        """\
        OTHER = {
            "handlers": {
                "mail_admins": {
                    "class": "django.utils.log.AdminEmailHandler",
                    "email_backend": "myapp.backends.EmailBackend",
                },
            },
        }
        """,
        filename="settings.py",
    )


def test_not_dict():
    check_noop(
        """\
        LOGGING = get_logging_config()
        """,
        filename="settings.py",
    )


def test_email_backend_not_in_handlers():
    check_noop(
        """\
        LOGGING = {
            "filters": {
                "special": {
                    "class": "django.utils.log.AdminEmailHandler",
                    "email_backend": "myapp.backends.EmailBackend",
                },
            },
        }
        """,
        filename="settings.py",
    )


def test_handler_value_not_dict():
    check_noop(
        """\
        LOGGING = {
            "handlers": {
                "mail_admins": get_handler(),
            },
        }
        """,
        filename="settings.py",
    )


def test_no_admin_email_handler():
    check_noop(
        """\
        LOGGING = {
            "handlers": {
                "console": {
                    "class": "logging.StreamHandler",
                    "email_backend": "myapp.backends.EmailBackend",
                },
            },
        }
        """,
        filename="settings.py",
    )


def test_no_email_backend():
    check_noop(
        """\
        LOGGING = {
            "handlers": {
                "mail_admins": {
                    "class": "django.utils.log.AdminEmailHandler",
                },
            },
        }
        """,
        filename="settings.py",
    )


def test_already_using():
    check_noop(
        """\
        LOGGING = {
            "handlers": {
                "mail_admins": {
                    "class": "django.utils.log.AdminEmailHandler",
                    "using": "admin-logging",
                },
            },
        }
        """,
        filename="settings.py",
    )


def test_success():
    check_transformed(
        """\
        LOGGING = {
            "handlers": {
                "mail_admins": {
                    "class": "django.utils.log.AdminEmailHandler",
                    "email_backend": "myapp.backends.EmailBackend",
                },
            },
        }
        """,
        """\
        LOGGING = {
            "handlers": {
                "mail_admins": {
                    "class": "django.utils.log.AdminEmailHandler",
                    "using": "myapp.backends.EmailBackend",
                },
            },
        }
        """,
        filename="settings.py",
    )


def test_success_single_quotes():
    check_transformed(
        """\
        LOGGING = {
            'handlers': {
                'mail_admins': {
                    'class': 'django.utils.log.AdminEmailHandler',
                    'email_backend': 'myapp.backends.EmailBackend',
                },
            },
        }
        """,
        """\
        LOGGING = {
            'handlers': {
                'mail_admins': {
                    'class': 'django.utils.log.AdminEmailHandler',
                    'using': 'myapp.backends.EmailBackend',
                },
            },
        }
        """,
        filename="settings.py",
    )


def test_success_multiple_handlers():
    check_transformed(
        """\
        LOGGING = {
            "handlers": {
                "mail_admins_1": {
                    "class": "django.utils.log.AdminEmailHandler",
                    "email_backend": "myapp.backends.Email1",
                },
                "mail_admins_2": {
                    "class": "django.utils.log.AdminEmailHandler",
                    "email_backend": "myapp.backends.Email2",
                },
            },
        }
        """,
        """\
        LOGGING = {
            "handlers": {
                "mail_admins_1": {
                    "class": "django.utils.log.AdminEmailHandler",
                    "using": "myapp.backends.Email1",
                },
                "mail_admins_2": {
                    "class": "django.utils.log.AdminEmailHandler",
                    "using": "myapp.backends.Email2",
                },
            },
        }
        """,
        filename="settings.py",
    )


def test_success_class_settings():
    check_transformed(
        """\
        class Settings:
            LOGGING = {
                "handlers": {
                    "mail_admins": {
                        "class": "django.utils.log.AdminEmailHandler",
                        "email_backend": "myapp.backends.EmailBackend",
                    },
                },
            }
            OTHER = True
        """,
        """\
        class Settings:
            LOGGING = {
                "handlers": {
                    "mail_admins": {
                        "class": "django.utils.log.AdminEmailHandler",
                        "using": "myapp.backends.EmailBackend",
                    },
                },
            }
            OTHER = True
        """,
        filename="settings.py",
    )

from __future__ import annotations

from functools import partial

from django_upgrade.data import Settings
from tests.fixers import tools

settings = Settings(target_version=(1, 9))
check_noop = partial(tools.check_noop, settings=settings)
check_transformed = partial(tools.check_transformed, settings=settings)


def test_not_settings_file():
    check_noop(
        """\
        DATABASES = {
            "default": {
                "ENGINE": "django.db.backends.postgresql_psycopg2",
                "NAME": "mydatabase",
            }
        }
        """,
    )


def test_wrong_engine():
    check_noop(
        """\
        DATABASES = {
            "default": {
                "ENGINE": "django.db.backends.sqlite3",
                "NAME": "mydatabase",
            }
        }
        """,
        filename="myapp/settings.py",
    )


def test_wrong_setting():
    check_noop(
        """\
        CACHES = {
            "default": {
                "BACKEND": "django.core.cache.backends.redis.RedisCache",
                "LOCATION": "redis://127.0.0.1:6379",
            }
        }
        """,
        filename="myapp/settings.py",
    )


def test_already_up_to_date():
    check_noop(
        """\
        DATABASES = {
            "default": {
                "ENGINE": "django.db.backends.postgresql",
                "NAME": "mydatabase",
            }
        }
        """,
        filename="myapp/settings.py",
    )


def test_success():
    check_transformed(
        """\
        DATABASES = {
            "default": {
                "ENGINE": "django.db.backends.postgresql_psycopg2",
                "NAME": "mydatabase",
                "USER": "mydatabaseuser",
                "PASSWORD": "mypassword",
                "HOST": "127.0.0.1",
                "PORT": "5432",
            }
        }
        """,
        """\
        DATABASES = {
            "default": {
                "ENGINE": "django.db.backends.postgresql",
                "NAME": "mydatabase",
                "USER": "mydatabaseuser",
                "PASSWORD": "mypassword",
                "HOST": "127.0.0.1",
                "PORT": "5432",
            }
        }
        """,
        filename="myapp/settings.py",
    )


def test_success_two_databases():
    check_transformed(
        """\
        DATABASES = {
            "default": {
                "ENGINE": "django.db.backends.postgresql_psycopg2",
            },
            "analytics": {"ENGINE": 'django.db.backends.postgresql_psycopg2'},
        }
        """,
        """\
        DATABASES = {
            "default": {
                "ENGINE": "django.db.backends.postgresql",
            },
            "analytics": {"ENGINE": 'django.db.backends.postgresql'},
        }
        """,
        filename="myapp/settings.py",
    )


def test_success_with_merged_settings():
    check_transformed(
        """\
        from settings import Base

        DATABASES = {
            **Base.DATABASE,
            "default": {
                "ENGINE": "django.db.backends.postgresql_psycopg2",
                "NAME": "mydatabase",
                "USER": "mydatabaseuser",
                "PASSWORD": "mypassword",
                "HOST": "127.0.0.1",
                "PORT": "5432",
            }
        }
        """,
        """\
        from settings import Base

        DATABASES = {
            **Base.DATABASE,
            "default": {
                "ENGINE": "django.db.backends.postgresql",
                "NAME": "mydatabase",
                "USER": "mydatabaseuser",
                "PASSWORD": "mypassword",
                "HOST": "127.0.0.1",
                "PORT": "5432",
            }
        }
        """,
        filename="myapp/settings.py",
    )


def test_success_class_based():
    check_transformed(
        """\
        class BaseSettings:
            DATABASES = {
                "default": {
                    "ENGINE": "django.db.backends.postgresql_psycopg2",
                    "NAME": "mydatabase",
                    "USER": "mydatabaseuser",
                    "PASSWORD": "mypassword",
                    "HOST": "127.0.0.1",
                    "PORT": "5432",
                }
            }
        """,
        """\
        class BaseSettings:
            DATABASES = {
                "default": {
                    "ENGINE": "django.db.backends.postgresql",
                    "NAME": "mydatabase",
                    "USER": "mydatabaseuser",
                    "PASSWORD": "mypassword",
                    "HOST": "127.0.0.1",
                    "PORT": "5432",
                }
            }
        """,
        filename="myapp/settings.py",
    )


def test_success_class_based_inherited():
    check_transformed(
        """\
        class BaseSettings:
            DATABASES = {
                "default": {
                    "ENGINE": "django.db.backends.postgresql_psycopg2",
                    "NAME": "mydatabase",
                    "USER": "mydatabaseuser",
                    "PASSWORD": "mypassword",
                    "HOST": "127.0.0.1",
                    "PORT": "5432",
                }
            }

        class DevSettings(BaseSettings):
            DATABASES = {
                "default": {
                    "ENGINE": "django.db.backends.sqlite3",
                    "NAME": "mydatabase",
                }
            }
        """,
        """\
        class BaseSettings:
            DATABASES = {
                "default": {
                    "ENGINE": "django.db.backends.postgresql",
                    "NAME": "mydatabase",
                    "USER": "mydatabaseuser",
                    "PASSWORD": "mypassword",
                    "HOST": "127.0.0.1",
                    "PORT": "5432",
                }
            }

        class DevSettings(BaseSettings):
            DATABASES = {
                "default": {
                    "ENGINE": "django.db.backends.sqlite3",
                    "NAME": "mydatabase",
                }
            }
        """,
        filename="myapp/settings.py",
    )

from __future__ import annotations

from django_upgrade.data import Settings
from tests.fixers.tools import check_noop, check_transformed

settings = Settings(target_version=(1, 9))


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
        settings,
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
        settings,
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
        settings,
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
        settings,
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
        settings,
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
        settings,
        filename="myapp/settings.py",
    )

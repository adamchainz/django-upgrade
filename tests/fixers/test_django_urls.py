from __future__ import annotations

from django_upgrade.data import Settings
from tests.fixers.tools import check_noop, check_transformed

settings = Settings(target_version=(2, 2))


def test_unrecognized_import_format():
    check_noop(
        """\
        from django.conf import urls

        urls.url("hahaha")
        """,
        settings,
    )


def test_alias_not_supported():
    check_noop(
        """\
        from django.conf.urls import url as u

        u("hahaha")
        """,
        settings,
    )


def test_unrecognized_name():
    check_noop(
        """\
        from django.conf.urls import something
        """,
        settings,
    )


def test_include():
    check_transformed(
        """\
        from django.conf.urls import include

        include('example.urls')
        """,
        """\
        from django.urls import include

        include('example.urls')
        """,
        settings,
    )


def test_url_not_used():
    check_noop(
        """\
        from django.conf.urls import url
        """,
        settings,
    )


def test_url_unsupported_call_format():
    check_noop(
        """\
        from django.conf.urls import url

        url(regex=r"^$", views.index)
        """,
        settings,
    )


def test_re_path_unconverted_regex():
    check_transformed(
        """\
        from django.conf.urls import url

        url(r'^[abc]{123}$', views.example)
        """,
        """\
        from django.urls import re_path

        re_path(r'^[abc]{123}$', views.example)
        """,
        settings,
    )


def test_re_path_translation():
    check_transformed(
        """\
        from django.conf.urls import url
        from django.utils.translation import gettext_lazy as _

        url(_(r'^about/$'), views.about)
        """,
        """\
        from django.urls import re_path
        from django.utils.translation import gettext_lazy as _

        re_path(_(r'^about/$'), views.about)
        """,
        settings,
    )


def test_re_path_variable():
    check_transformed(
        """\
        from django.conf.urls import url

        path = r'^$'
        url(path, views.index)
        """,
        """\
        from django.urls import re_path

        path = r'^$'
        re_path(path, views.index)
        """,
        settings,
    )


def test_path_empty():
    check_transformed(
        """\
        from django.conf.urls import url

        url(r"^$", views.index)
        """,
        """\
        from django.urls import path

        path('', views.index)
        """,
        settings,
    )


def test_path_simple():
    check_transformed(
        """\
        from django.conf.urls import url

        url(r'^about/$', views.about, name='about')
        """,
        """\
        from django.urls import path

        path('about/', views.about, name='about')
        """,
        settings,
    )


def test_path_unanchored_start():
    check_transformed(
        """\
        from django.conf.urls import url

        url(r'about/$', views.about)
        """,
        """\
        from django.urls import path

        path('about/', views.about)
        """,
        settings,
    )


def test_path_unanchored_end():
    check_transformed(
        """\
        from django.conf.urls import url

        url(r'^weblog/', views.blog)
        """,
        """\
        from django.urls import path

        path('weblog/', views.blog)
        """,
        settings,
    )


def test_path_with_dash():
    check_transformed(
        """\
        from django.conf.urls import url

        url(r'^more-info/$', views.more_info)
        """,
        """\
        from django.urls import path

        path('more-info/', views.more_info)
        """,
        settings,
    )


def test_path_int_converter_1():
    check_transformed(
        """\
        from django.conf.urls import url

        url(r'^page/(?P<number>[0-9]+)/$', views.page)
        """,
        """\
        from django.urls import path

        path('page/<int:number>/', views.page)
        """,
        settings,
    )


def test_path_int_converter_2():
    check_transformed(
        """\
        from django.conf.urls import url

        url(r'^page/(?P<number>\\d+)/$', views.page)
        """,
        """\
        from django.urls import path

        path('page/<int:number>/', views.page)
        """,
        settings,
    )


def test_path_path_converter():
    check_transformed(
        """\
        from django.conf.urls import url

        url(r'^(?P<subpath>.+)/$', views.default)
        """,
        """\
        from django.urls import path

        path('<path:subpath>/', views.default)
        """,
        settings,
    )


def test_path_slug_converter():
    check_transformed(
        """\
        from django.conf.urls import url

        url(r'^post/(?P<slug>[-a-zA-Z0-9_]+)/$', views.post)
        """,
        """\
        from django.urls import path

        path('post/<slug:slug>/', views.post)
        """,
        settings,
    )


def test_path_str_converter():
    check_transformed(
        """\
        from django.conf.urls import url

        url(r'^about/(?P<name>[^/]+)/$', views.about)
        """,
        """\
        from django.urls import path

        path('about/<str:name>/', views.about)
        """,
        settings,
    )


def test_path_uuid_converter():
    uuid_re = "[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}"
    check_transformed(
        f"""\
        from django.conf.urls import url

        url(r'^uuid/(?P<uuid>{uuid_re})/$', by_uuid)
        """,
        """\
        from django.urls import path

        path('uuid/<uuid:uuid>/', by_uuid)
        """,
        settings,
    )


def test_complete():
    check_transformed(
        """\
        from django.conf.urls import include, url

        urlpatterns = [
            url(r'^$', views.index, name='index'),
            url(r'^about/$', views.about, name='about'),
            url(r'^post/(?P<slug>[w-]+)/$', views.post, name='post'),
            url(r'^weblog/', include('blog.urls')),
        ]
        """,
        """\
        from django.urls import include, path, re_path

        urlpatterns = [
            path('', views.index, name='index'),
            path('about/', views.about, name='about'),
            re_path(r'^post/(?P<slug>[w-]+)/$', views.post, name='post'),
            path('weblog/', include('blog.urls')),
        ]
        """,
        settings,
    )

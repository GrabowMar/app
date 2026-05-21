from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.urls import include
from django.urls import path
from django.urls import re_path
from django.views import defaults as default_views

from llm_lab.realtime.api.views import sse_stream
from llm_lab.runtime.proxy import app_proxy_view
from llm_lab.runtime.proxy import app_redirect_to_root

from .api import api

urlpatterns = [
    # Django Admin, use {% url 'admin:index' %}
    path(settings.ADMIN_URL, admin.site.urls),
    # User management
    path("users/", include("llm_lab.users.urls", namespace="users")),
    path("accounts/", include("allauth.urls")),
    path("_allauth/", include("allauth.headless.urls")),
    # Reverse-proxy for scaffolded apps. Subdomain is a job hex prefix
    # (8–12 chars). The redirect ensures relative asset URLs resolve.
    re_path(
        r"^app/(?P<subdomain>[0-9a-f]{8,12})$",
        app_redirect_to_root,
        name="app-proxy-redirect",
    ),
    re_path(
        r"^app/(?P<subdomain>[0-9a-f]{8,12})/(?P<rest>.*)$",
        app_proxy_view,
        name="app-proxy",
    ),
    # Media files
    *static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT),
]
if settings.DEBUG:
    # Static file serving when using Gunicorn + Uvicorn for local web socket development
    urlpatterns += staticfiles_urlpatterns()


# API URLS
urlpatterns += [
    # API base url
    path("api/", api.urls),
    # Realtime SSE stream (plain Django view — Ninja doesn't support streaming)
    path("api/realtime/stream", sse_stream),
]

if settings.DEBUG:
    # This allows the error pages to be debugged during development, just visit
    # these url in browser to see how these error pages look like.
    urlpatterns += [
        path(
            "400/",
            default_views.bad_request,
            kwargs={"exception": Exception("Bad Request!")},
        ),
        path(
            "403/",
            default_views.permission_denied,
            kwargs={"exception": Exception("Permission Denied")},
        ),
        path(
            "404/",
            default_views.page_not_found,
            kwargs={"exception": Exception("Page not Found")},
        ),
        path("500/", default_views.server_error),
    ]
    if "debug_toolbar" in settings.INSTALLED_APPS:
        import debug_toolbar

        urlpatterns = [
            path("__debug__/", include(debug_toolbar.urls)),
            *urlpatterns,
        ]

"""Reverse-proxy view that serves running ContainerInstances under /app/<id>/.

The proxy forwards the path with the ``/app/<id>`` prefix stripped, so the
container always sees URLs as if it were mounted at root. To make
absolute-path references in generated HTML still resolve under the proxied
prefix we:

* inject ``<base href="/app/<id>/">`` after ``<head>`` in HTML responses, and
* rewrite ``Location:`` headers that begin with a single ``/`` so server-side
  redirects don't break out of the proxied namespace.

Generated SPAs are built with Vite ``base: './'`` (relative asset URLs) and
read their proxy prefix at runtime from ``window.location.pathname``. They
never need to know they're behind a proxy at build time.
"""

from __future__ import annotations

import contextlib
import logging
import re
from urllib import error as urllib_error
from urllib import request as urllib_request

from django.contrib.auth import get_user
from django.http import HttpRequest
from django.http import HttpResponse
from django.http import HttpResponsePermanentRedirect
from django.http import JsonResponse
from django.http import StreamingHttpResponse
from django.views.decorators.csrf import csrf_exempt

from llm_lab.runtime.models import ContainerInstance
from llm_lab.runtime.services import docker_manager

logger = logging.getLogger(__name__)

_HOP_BY_HOP = frozenset(
    {
        "connection", "keep-alive", "proxy-authenticate", "proxy-authorization",
        "te", "trailer", "trailers", "transfer-encoding", "upgrade",
    },
)
_STRIP_REQ = frozenset({"cookie", "authorization", "x-csrftoken", "host", "content-length", "accept-encoding"})
_STRIP_RESP = frozenset({"set-cookie", "set-cookie2", "content-length"})

_CHUNK_SIZE = 8 * 1024
_TIMEOUT = 30
_INTERNAL_PORT = 80
_HTML_MAX_BUFFER = 4 * 1024 * 1024  # only buffer-rewrite HTML up to 4 MiB

_HEAD_OPEN_RE = re.compile(rb"<head(\s[^>]*)?>", re.IGNORECASE)


def _resolve_container_address(container: ContainerInstance) -> str | None:
    c = docker_manager.client()
    if c is None:
        return None
    try:
        dc = c.containers.get(container.name)
    except Exception as exc:  # noqa: BLE001
        logger.warning("proxy: docker get(%s) failed: %s", container.name, exc)
        return None
    try:
        dc.reload()
        nets = dc.attrs.get("NetworkSettings", {})
        ip = nets.get("IPAddress")
        if not ip:
            for net in (nets.get("Networks") or {}).values():
                if net.get("IPAddress"):
                    ip = net["IPAddress"]
                    break
        if not ip:
            return None
    except Exception as exc:  # noqa: BLE001
        logger.warning("proxy: inspect(%s) failed: %s", container.name, exc)
        return None
    return f"{ip}:{_INTERNAL_PORT}"


def _inject_base_href(body: bytes, prefix: str) -> bytes:
    """Insert ``<base href="<prefix>">`` after the opening ``<head>`` tag."""
    if not body or b"<head" not in body[:8192].lower():
        # Best-effort: skip injection if there's no <head>.
        return body
    base_tag = f'<base href="{prefix}">'.encode("utf-8")
    if base_tag in body:
        return body

    def _sub(match: re.Match[bytes]) -> bytes:
        return match.group(0) + base_tag

    new, n = _HEAD_OPEN_RE.subn(_sub, body, count=1)
    return new if n else body


@csrf_exempt
def app_proxy_view(
    request: HttpRequest,
    subdomain: str,
    rest: str = "",
) -> HttpResponse:
    """Proxy ``/app/<subdomain>/<rest>`` to the container's port 80."""
    user = get_user(request)
    if not user.is_authenticated:
        return JsonResponse({"detail": "Authentication required"}, status=401)

    try:
        container = ContainerInstance.objects.get(subdomain=subdomain)
    except ContainerInstance.DoesNotExist:
        return JsonResponse({"detail": "App not found"}, status=404)

    if container.status != ContainerInstance.Status.RUNNING:
        return JsonResponse(
            {"detail": "App is not running", "status": container.status},
            status=503,
        )

    address = _resolve_container_address(container)
    if not address:
        return JsonResponse({"detail": "App network address unavailable"}, status=503)

    prefix = f"/app/{subdomain}/"
    upstream_path = "/" + rest
    qs = request.META.get("QUERY_STRING", "")
    if qs:
        upstream_path = f"{upstream_path}?{qs}"
    upstream_url = f"http://{address}{upstream_path}"

    body = request.body if request.method not in ("GET", "HEAD", "OPTIONS") else None
    req = urllib_request.Request(  # noqa: S310 - target is a docker-network IP
        url=upstream_url,
        data=body,
        method=request.method or "GET",
    )
    for key, value in request.headers.items():
        lower = key.lower()
        if lower in _HOP_BY_HOP or lower in _STRIP_REQ:
            continue
        req.add_header(key, value)
    req.add_header("X-Forwarded-For", request.META.get("REMOTE_ADDR", ""))
    req.add_header("X-Forwarded-Proto", "https" if request.is_secure() else "http")
    req.add_header("X-Forwarded-Host", request.get_host())
    req.add_header("X-Forwarded-Prefix", prefix.rstrip("/"))
    req.add_header("X-App-Proxy", "llm-lab")

    try:
        upstream = urllib_request.urlopen(req, timeout=_TIMEOUT)  # noqa: S310
    except urllib_error.HTTPError as e:
        upstream = e
    except (urllib_error.URLError, TimeoutError, ConnectionError) as e:
        logger.warning("App proxy upstream failure for %s: %s", subdomain, e)
        return JsonResponse({"detail": "App unreachable", "error": str(e)}, status=502)

    status = upstream.status if hasattr(upstream, "status") else upstream.getcode()
    upstream_headers = dict(upstream.headers.items())
    content_type = ""
    for k, v in upstream_headers.items():
        if k.lower() == "content-type":
            content_type = v.lower()
            break

    is_html = content_type.startswith("text/html")
    try:
        content_length = int(upstream_headers.get("Content-Length") or 0)
    except (TypeError, ValueError):
        content_length = 0
    buffer_for_rewrite = is_html and (content_length == 0 or content_length <= _HTML_MAX_BUFFER)

    def _filter_headers(resp: HttpResponse) -> None:
        for key, value in upstream_headers.items():
            lower = key.lower()
            if lower in _HOP_BY_HOP or lower in _STRIP_RESP:
                continue
            if lower == "location" and value.startswith("/") and not value.startswith("//"):
                # Keep server-issued redirects inside the proxy namespace.
                value = prefix.rstrip("/") + value
            resp[key] = value

    if buffer_for_rewrite:
        try:
            data = upstream.read()
        finally:
            with contextlib.suppress(Exception):
                upstream.close()
        rewritten = _inject_base_href(data, prefix)
        response = HttpResponse(rewritten, status=status)
        _filter_headers(response)
        # Ensure Content-Length reflects the rewritten body.
        response["Content-Length"] = str(len(rewritten))
        return response

    def _stream():
        try:
            while True:
                chunk = upstream.read(_CHUNK_SIZE)
                if not chunk:
                    break
                yield chunk
        finally:
            with contextlib.suppress(Exception):
                upstream.close()

    response = StreamingHttpResponse(_stream(), status=status)
    _filter_headers(response)
    return response


def app_redirect_to_root(request: HttpRequest, subdomain: str) -> HttpResponse:
    """Redirect /app/<subdomain> → /app/<subdomain>/."""
    return HttpResponsePermanentRedirect(f"/app/{subdomain}/")

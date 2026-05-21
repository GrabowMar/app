"""Tests for the /app/<subdomain>/ reverse-proxy view."""

from __future__ import annotations

from io import BytesIO
from unittest.mock import patch

import pytest
from django.test import Client  # noqa: TC002

from llm_lab.runtime.models import ContainerInstance
from llm_lab.runtime.tests.factories import ContainerInstanceFactory
from llm_lab.users.tests.factories import UserFactory


class _FakeUpstream:
    def __init__(self, body: bytes = b"<html>ok</html>", status: int = 200,
                 headers: dict | None = None):
        self._buf = BytesIO(body)
        self.status = status
        self.headers = headers or {"Content-Type": "text/html; charset=utf-8"}

    def read(self, n: int = -1) -> bytes:
        return self._buf.read(n)

    def getcode(self) -> int:
        return self.status

    def close(self) -> None:
        self._buf.close()


@pytest.mark.django_db
class TestAppProxyView:
    def test_unauthenticated_returns_401(self, client: Client):
        ContainerInstanceFactory(
            subdomain="abcd1234",
            status=ContainerInstance.Status.RUNNING,
            frontend_port=5000,
        )
        resp = client.get("/app/abcd1234/")
        assert resp.status_code == 401

    def test_unknown_subdomain_returns_404(self, client: Client):
        client.force_login(UserFactory())
        resp = client.get("/app/deadbeef/")
        assert resp.status_code == 404

    def test_not_running_returns_503(self, client: Client):
        ContainerInstanceFactory(
            subdomain="abcd1234",
            status=ContainerInstance.Status.STOPPED,
            frontend_port=5000,
        )
        client.force_login(UserFactory())
        resp = client.get("/app/abcd1234/")
        assert resp.status_code == 503

    def test_happy_path_forwards_and_strips_set_cookie(self, client: Client):
        ContainerInstanceFactory(
            subdomain="abcd1234",
            status=ContainerInstance.Status.RUNNING,
            frontend_port=5000,
        )
        client.force_login(UserFactory())
        fake = _FakeUpstream(
            body=b"<html><head><title>x</title></head><body>weather</body></html>",
            headers={
                "Content-Type": "text/html",
                "Set-Cookie": "evil=1; Path=/",
                "X-Custom": "yes",
            },
        )
        with patch(
            "llm_lab.runtime.proxy._resolve_container_address",
            return_value="172.17.0.5:80",
        ), patch(
            "llm_lab.runtime.proxy.urllib_request.urlopen", return_value=fake,
        ) as m:
            resp = client.get("/app/abcd1234/some/page?q=1")
        assert resp.status_code == 200
        assert b"weather" in resp.content
        assert b'<base href="/app/abcd1234/">' in resp.content
        assert "Set-Cookie" not in resp
        assert resp.get("X-Custom") == "yes"
        called_url = m.call_args[0][0].full_url
        assert called_url == "http://172.17.0.5:80/some/page?q=1"

    def test_root_request_forwards_to_slash(self, client: Client):
        ContainerInstanceFactory(
            subdomain="abcd1234",
            status=ContainerInstance.Status.RUNNING,
            frontend_port=5000,
        )
        client.force_login(UserFactory())
        with patch(
            "llm_lab.runtime.proxy._resolve_container_address",
            return_value="172.17.0.5:80",
        ), patch(
            "llm_lab.runtime.proxy.urllib_request.urlopen",
            return_value=_FakeUpstream(),
        ) as m:
            client.get("/app/abcd1234/")
        assert m.call_args[0][0].full_url == "http://172.17.0.5:80/"

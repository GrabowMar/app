"""Legacy dynamic analyzers ported from the old analysis stack."""

from __future__ import annotations

import json
import logging
import socket
import ssl
import time
import urllib.error
import urllib.request
from typing import TYPE_CHECKING
from typing import Any
from typing import ClassVar
from urllib.parse import urlparse

from llm_lab.analysis.services.base import AnalyzerOutput
from llm_lab.analysis.services.base import BaseAnalyzer
from llm_lab.analysis.services.base import FindingData
from llm_lab.analysis.services.dynamic._common import _slug
from llm_lab.analysis.services.live_target import join_target_url
from llm_lab.analysis.services.live_target import resolve_target_url

if TYPE_CHECKING:
    from llm_lab.analysis.services.cancellation import CancellationToken

logger = logging.getLogger(__name__)

_DEFAULT_SCAN_PORTS = [21, 22, 25, 53, 80, 443, 3306, 5432, 6379, 8080, 8443]
_SERVICE_NAMES = {
    21: "FTP",
    22: "SSH",
    25: "SMTP",
    53: "DNS",
    80: "HTTP",
    443: "HTTPS",
    3306: "MySQL",
    5432: "PostgreSQL",
    6379: "Redis",
    8080: "HTTP alternate",
    8443: "HTTPS alternate",
}


def _request_url(
    url: str,
    *,
    method: str = "GET",
    timeout: int = 10,
    verify_ssl: bool = True,
    user_agent: str = "",
    body: dict[str, Any] | None = None,
) -> tuple[int | None, dict[str, str], str, float, str | None]:
    data = None
    headers = {"Content-Type": "application/json"}
    if user_agent:
        headers["User-Agent"] = user_agent
    if body is not None:
        data = json.dumps(body).encode()
    if not verify_ssl:
        return None, {}, "", 0.0, "verify_ssl=False is not supported by the analyzer runtime"

    request = urllib.request.Request(url, data=data, headers=headers, method=method)  # noqa: S310
    started = time.perf_counter()
    try:
        with urllib.request.urlopen(request, timeout=timeout, context=ssl.create_default_context()) as response:  # noqa: S310
            duration_ms = round((time.perf_counter() - started) * 1000, 2)
            payload = response.read(4096).decode("utf-8", errors="ignore")
            return response.status, dict(response.headers.items()), payload, duration_ms, None
    except urllib.error.HTTPError as exc:
        duration_ms = round((time.perf_counter() - started) * 1000, 2)
        return exc.code, dict(exc.headers.items()), exc.read(4096).decode("utf-8", errors="ignore"), duration_ms, None
    except OSError as exc:
        duration_ms = round((time.perf_counter() - started) * 1000, 2)
        return None, {}, "", duration_ms, str(exc)


class CurlAnalyzer(BaseAnalyzer):
    name: ClassVar[str] = "curl"
    analyzer_type: ClassVar[str] = "dynamic"
    display_name: ClassVar[str] = "cURL HTTP Client"
    description: ClassVar[str] = "HTTP connectivity and response testing for live applications"
    default_config: ClassVar[dict[str, Any]] = {
        "timeout": 10,
        "verify_ssl": True,
        "user_agent": "LLM Eval Lab Analysis",
    }

    def check_available(self) -> tuple[bool, str]:
        return True, "Available (uses Python HTTP client)"

    def analyze(
        self,
        code: dict[str, str],
        config: dict[str, Any] | None = None,
        *,
        cancel: CancellationToken | None = None,
    ) -> AnalyzerOutput:
        del code, cancel
        merged = {**self.default_config, **(config or {})}
        target_url, error = resolve_target_url(merged)
        if error:
            return AnalyzerOutput(error=f"cURL analysis requires a live target: {error}")

        status, headers, payload, duration_ms, request_error = _request_url(
            target_url,
            timeout=int(merged["timeout"]),
            verify_ssl=bool(merged["verify_ssl"]),
            user_agent=str(merged["user_agent"]),
        )
        if request_error:
            return AnalyzerOutput(error=f"Request failed: {request_error}")

        findings: list[FindingData] = []
        if status is None:
            return AnalyzerOutput(error="No HTTP response received")
        if status >= 500:
            findings.append(
                FindingData(
                    severity="high",
                    category="quality",
                    title="Server returned a 5xx response",
                    description=f"The target returned HTTP {status}.",
                    suggestion="Inspect the deployed application logs and fix the server-side error.",
                    rule_id="curl/http-5xx",
                    confidence="high",
                ),
            )
        elif status >= 400:
            findings.append(
                FindingData(
                    severity="medium",
                    category="quality",
                    title="Target returned a client error response",
                    description=f"The target returned HTTP {status}.",
                    suggestion="Verify the deployed route exists and accepts this request.",
                    rule_id="curl/http-4xx",
                    confidence="high",
                ),
            )

        security_headers = {
            "content-security-policy": "Content-Security-Policy header missing",
            "x-content-type-options": "X-Content-Type-Options header missing",
            "x-frame-options": "X-Frame-Options header missing",
        }
        lowered_headers = {name.lower(): value for name, value in headers.items()}
        for header_name, title in security_headers.items():
            if header_name not in lowered_headers:
                findings.append(
                    FindingData(
                        severity="low",
                        category="security",
                        title=title,
                        description=f"The response does not include {header_name}.",
                        suggestion=f"Set the {header_name} response header.",
                        rule_id=f"curl/{header_name}",
                        confidence="medium",
                    ),
                )
        if duration_ms > 2000:
            findings.append(
                FindingData(
                    severity="medium",
                    category="performance",
                    title="Slow endpoint response",
                    description=f"Initial request took {duration_ms} ms.",
                    suggestion="Profile the endpoint and reduce expensive backend work on the critical path.",
                    rule_id="curl/slow-response",
                    confidence="medium",
                ),
            )

        return AnalyzerOutput(
            findings=findings,
            summary={
                "status_code": status,
                "response_time_ms": duration_ms,
                "response_size_bytes": len(payload.encode("utf-8", errors="ignore")),
            },
            raw_output={"headers": headers, "body_preview": payload[:1000]},
        )


class NmapAnalyzer(BaseAnalyzer):
    name: ClassVar[str] = "nmap"
    analyzer_type: ClassVar[str] = "dynamic"
    display_name: ClassVar[str] = "Nmap Network Scanner"
    description: ClassVar[str] = "TCP service exposure scan for a live target"
    default_config: ClassVar[dict[str, Any]] = {
        "ports": _DEFAULT_SCAN_PORTS,
        "timeout": 1,
    }

    def check_available(self) -> tuple[bool, str]:
        return True, "Available (uses Python socket scans)"

    def analyze(
        self,
        code: dict[str, str],
        config: dict[str, Any] | None = None,
        *,
        cancel: CancellationToken | None = None,
    ) -> AnalyzerOutput:
        del code
        merged = {**self.default_config, **(config or {})}
        target_url = None
        target_host = str(merged.get("target_host") or "").strip()
        if not target_host:
            target_url, error = resolve_target_url(merged)
            if error:
                return AnalyzerOutput(error=f"Nmap scan requires a live target: {error}")
            parsed = urlparse(target_url)
            target_host = parsed.hostname or ""
            if parsed.port:
                merged["ports"] = sorted({parsed.port, *list(merged["ports"])})
        else:
            blocked_hosts = {"localhost", "127.0.0.1", "0.0.0.0", "::1", "169.254.169.254"}  # noqa: S104
            if target_host.lower() in blocked_hosts and not merged.get("live_target"):
                return AnalyzerOutput(error=f"Blocked host: {target_host}")

        findings: list[FindingData] = []
        open_ports: list[int] = []
        for port in list(merged["ports"]):
            if cancel is not None and cancel.is_cancelled():
                return AnalyzerOutput(error="Analysis cancelled")
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.settimeout(float(merged["timeout"]))
                is_open = sock.connect_ex((target_host, int(port))) == 0
            if not is_open:
                continue
            open_ports.append(int(port))
            service_name = _SERVICE_NAMES.get(int(port), "Unknown service")
            severity = "high" if int(port) in {21, 3306, 5432, 6379} else "medium" if int(port) in {22, 25} else "low"
            findings.append(
                FindingData(
                    severity=severity,
                    category="security",
                    title=f"Open port {port} ({service_name})",
                    description=f"Port {port} is reachable on {target_host}.",
                    suggestion="Restrict externally exposed services to only the ports required for the application.",
                    rule_id=f"nmap/{port}",
                    confidence="high",
                    tool_specific_data={"service": service_name, "host": target_host},
                ),
            )

        return AnalyzerOutput(
            findings=findings,
            summary={"target_host": target_host, "open_ports": open_ports, "open_ports_count": len(open_ports)},
            raw_output={"target_url": target_url},
        )


class CurlEndpointTesterAnalyzer(BaseAnalyzer):
    name: ClassVar[str] = "curl-endpoint-tester"
    analyzer_type: ClassVar[str] = "dynamic"
    display_name: ClassVar[str] = "Curl Endpoint Tester"
    description: ClassVar[str] = "HTTP endpoint validation against the generated app's expected API surface"
    default_config: ClassVar[dict[str, Any]] = {
        "timeout": 10,
    }

    def check_available(self) -> tuple[bool, str]:
        return True, "Available (uses Python HTTP client)"

    def analyze(
        self,
        code: dict[str, str],
        config: dict[str, Any] | None = None,
        *,
        cancel: CancellationToken | None = None,
    ) -> AnalyzerOutput:
        del code
        merged = {**self.default_config, **(config or {})}
        target_url, error = resolve_target_url(merged)
        if error:
            return AnalyzerOutput(error=f"Endpoint tests require a live target: {error}")

        endpoints = self._get_endpoints(merged)
        if not endpoints:
            return AnalyzerOutput(summary={"message": "No endpoints defined for testing"})

        findings: list[FindingData] = []
        passed = 0
        failed = 0
        raw_results: list[dict[str, Any]] = []
        for endpoint in endpoints:
            if cancel is not None and cancel.is_cancelled():
                return AnalyzerOutput(error="Analysis cancelled")
            request_url, join_error = join_target_url(target_url, str(endpoint.get("path") or "/"))
            if join_error or request_url is None:
                failed += 1
                findings.append(
                    FindingData(
                        severity="medium",
                        category="quality",
                        title="Invalid endpoint configuration",
                        description=join_error or "Could not build endpoint URL",
                        suggestion="Use a relative endpoint path such as /api/items.",
                        rule_id=f"endpoint/{_slug(str(endpoint.get('path') or 'unknown'))}",
                        confidence="high",
                    ),
                )
                continue

            expected = endpoint.get("expected_status")
            if isinstance(expected, int):
                expected_statuses = {expected}
            elif isinstance(expected, list):
                expected_statuses = {int(value) for value in expected}
            else:
                method = str(endpoint.get("method") or "GET").upper()
                expected_statuses = {200, 201, 204} if method in {"POST", "PUT", "PATCH", "DELETE"} else {200}

            status, headers, payload, duration_ms, request_error = _request_url(
                request_url,
                method=str(endpoint.get("method") or "GET").upper(),
                timeout=int(merged["timeout"]),
                verify_ssl=bool(merged.get("verify_ssl", True)),
                user_agent="LLM Eval Lab Endpoint Tester",
                body=endpoint.get("request_body") if isinstance(endpoint.get("request_body"), dict) else None,
            )
            raw_results.append(
                {
                    "path": endpoint.get("path"),
                    "method": endpoint.get("method", "GET"),
                    "status": status,
                    "duration_ms": duration_ms,
                    "error": request_error,
                    "headers": headers,
                    "body_preview": payload[:500],
                },
            )
            if request_error or status not in expected_statuses:
                failed += 1
                findings.append(
                    FindingData(
                        severity="high" if (status or 0) >= 500 or request_error else "medium",
                        category="quality",
                        title=f"Endpoint test failed: {endpoint.get('method', 'GET')} {endpoint.get('path', '/')}",
                        description=request_error or f"Expected {sorted(expected_statuses)}, got {status}.",
                        suggestion="Fix the route implementation or update the expected status code in the template.",
                        rule_id=(
                            f"endpoint/{_slug(str(endpoint.get('method', 'get')))}-"
                            f"{_slug(str(endpoint.get('path', '/')))}"
                        ),
                        confidence="high",
                    ),
                )
            else:
                passed += 1

        return AnalyzerOutput(
            findings=findings,
            summary={
                "passed": passed,
                "failed": failed,
                "total": len(endpoints),
            },
            raw_output={"results": raw_results},
        )

    def _get_endpoints(self, config: dict[str, Any]) -> list[dict[str, Any]]:
        if isinstance(config.get("endpoints"), list):
            normalized: list[dict[str, Any]] = []
            for item in config["endpoints"]:
                if isinstance(item, str):
                    normalized.append({"path": item, "method": "GET"})
                elif isinstance(item, dict):
                    normalized.append(item)
            if normalized:
                return normalized

        app_requirement_id = config.get("app_requirement_id")
        if not app_requirement_id:
            return []
        try:
            from llm_lab.generation.models import AppRequirementTemplate

            template = AppRequirementTemplate.objects.get(id=app_requirement_id)
        except AppRequirementTemplate.DoesNotExist:
            return []

        endpoints: list[dict[str, Any]] = []
        for endpoint in template.api_endpoints or []:
            if not isinstance(endpoint, dict):
                continue
            endpoints.append(
                {
                    "path": endpoint.get("path", "/"),
                    "method": endpoint.get("method", "GET"),
                    "expected_status": endpoint.get("expected_status"),
                    "request_body": endpoint.get("request"),
                    "description": endpoint.get("description", ""),
                },
            )
        return endpoints

"""Dynamic analysis tools — ZAP security scanner and port scanner."""

from __future__ import annotations

import contextlib
import json
import logging
import re
import shutil
import socket
import subprocess
from typing import Any
from typing import ClassVar

from llm_lab.analysis.services.base import AnalyzerOutput
from llm_lab.analysis.services.base import BaseAnalyzer
from llm_lab.analysis.services.base import FindingData

logger = logging.getLogger(__name__)

ZAP_RISK_TO_SEVERITY: dict[int, str] = {
    0: "info",
    1: "low",
    2: "medium",
    3: "high",
}

_ZAP_CONFIDENCE_HIGH = 3
_ZAP_CONFIDENCE_MEDIUM = 2

DANGEROUS_PORT_MAP: dict[int, tuple[str, str]] = {
    21: ("high", "FTP — unencrypted file transfer"),
    22: ("medium", "SSH — secure shell access"),
    23: ("high", "Telnet — unencrypted remote access"),
    25: ("medium", "SMTP — mail server"),
    53: ("low", "DNS — domain name service"),
    80: ("info", "HTTP — web server"),
    443: ("info", "HTTPS — secure web server"),
    3306: ("high", "MySQL — database exposed"),
    5432: ("high", "PostgreSQL — database exposed"),
    6379: ("high", "Redis — in-memory store exposed"),
    8080: ("low", "HTTP alt — development server"),
    8443: ("low", "HTTPS alt — development server"),
    27017: ("high", "MongoDB — database exposed"),
}

DEFAULT_SCAN_PORTS: list[int] = sorted(DANGEROUS_PORT_MAP.keys())

_SQL_INJECTION_PAT = (
    r"""(?i)(?:execute|cursor\.execute|raw\()"""
    r"""\s*\(\s*(?:f["']|["']\s*%\s*|["']\s*\.\s*format\s*\()"""
)

_STATIC_VULN_PATTERNS: list[tuple[str, str, str, str, str, str]] = [
    (
        _SQL_INJECTION_PAT,
        "Potential SQL injection",
        "String formatting used directly in a SQL query.",
        "Use parameterized queries or an ORM.",
        "high",
        "security",
    ),
    (
        r"""(?i)(?:innerHTML|outerHTML|document\.write)\s*[=(]""",
        "Potential XSS via DOM manipulation",
        "Direct DOM manipulation with user-controlled data.",
        "Use safe DOM APIs or framework escaping.",
        "high",
        "security",
    ),
    (
        r"""(?i)\{%\s*autoescape\s+off\s*%\}""",
        "Template auto-escaping disabled",
        "Disabling auto-escaping may introduce XSS.",
        "Keep auto-escaping enabled.",
        "high",
        "security",
    ),
    (
        r"""(?i)@csrf_exempt""",
        "CSRF protection disabled",
        "Endpoint is exempt from CSRF protection.",
        "Remove @csrf_exempt or add alternative protection.",
        "medium",
        "security",
    ),
    (
        r"""(?i)(?:api[_-]?key|secret[_-]?key|password|token"""
        r"""|aws[_-]?secret)\s*[:=]\s*["'][A-Za-z0-9+/=_\-]{8,}["']""",
        "Hardcoded secret or credential",
        "A secret value appears hardcoded in source code.",
        "Use environment variables or a secrets manager.",
        "critical",
        "security",
    ),
    (
        r"""(?i)CORS_ALLOW_ALL_ORIGINS\s*=\s*True"""
        r"""|Access-Control-Allow-Origin['":\s]+\*""",
        "Permissive CORS configuration",
        "Wildcard CORS allows any origin.",
        "Restrict CORS to specific trusted origins.",
        "medium",
        "security",
    ),
    (
        r"""(?i)DEBUG\s*=\s*True""",
        "Debug mode enabled",
        "Debug mode exposes sensitive error details.",
        "Ensure DEBUG is False in production.",
        "high",
        "security",
    ),
    (
        r"""(?i)(?:eval|exec)\s*\(""",
        "Use of eval/exec",
        "Dynamic code execution can introduce injection.",
        "Avoid eval/exec; use safer alternatives.",
        "high",
        "security",
    ),
    (
        r"""(?i)verify\s*=\s*False""",
        "SSL verification disabled",
        "Disabling SSL verification enables MITM attacks.",
        "Enable SSL certificate verification.",
        "medium",
        "security",
    ),
    (
        r"""(?i)pickle\.loads?\(""",
        "Insecure deserialization",
        "Pickle deserialization can execute arbitrary code.",
        "Use safe serialization formats like JSON.",
        "high",
        "security",
    ),
]

_PORT_CODE_PATTERNS: list[tuple[str, str, str, str, str]] = [
    (
        r"""0\.0\.0\.0""",
        "Service bound to all interfaces",
        "Binding to 0.0.0.0 exposes the service widely.",
        "Bind to 127.0.0.1 or a specific interface.",
        "medium",
    ),
    (
        r"""(?i)DEBUG\s*=\s*True""",
        "Debug mode enabled",
        "Debug mode may expose diagnostic endpoints.",
        "Disable debug mode in production.",
        "high",
    ),
    (
        r"""(?i)CORS_ALLOW_ALL_ORIGINS\s*=\s*True""",
        "CORS wildcard enabled",
        "All origins are allowed cross-origin requests.",
        "Restrict allowed origins to trusted domains.",
        "medium",
    ),
    (
        r"""(?i)ALLOWED_HOSTS\s*=\s*\[\s*["']\*["']\s*\]""",
        "Wildcard ALLOWED_HOSTS",
        "Any host header is accepted.",
        "Set ALLOWED_HOSTS to specific domain names.",
        "medium",
    ),
    (
        r""":(\d{4,5})(?:[/"'\s]|$)""",
        "Hardcoded port reference",
        "A port number is hardcoded in source code.",
        "Use config or env vars for port numbers.",
        "low",
    ),
]


class ZAPAnalyzer(BaseAnalyzer):
    """OWASP ZAP security scanner — runs ZAP baseline scan or static code analysis."""

    name: ClassVar[str] = "zap"
    analyzer_type: ClassVar[str] = "dynamic"
    display_name: ClassVar[str] = "OWASP ZAP Security Scanner"
    description: ClassVar[str] = (
        "Scans web applications for security vulnerabilities"
        " using OWASP ZAP baseline scan"
    )

    def check_available(self) -> tuple[bool, str]:
        if shutil.which("docker") is None:
            return False, "Docker is not installed or not on PATH"
        try:
            result = subprocess.run(
                ["docker", "info"],  # noqa: S607
                capture_output=True,
                text=True,
                timeout=10,
                check=False,
            )
            if result.returncode != 0:
                return False, "Docker daemon is not running"
        except (subprocess.TimeoutExpired, OSError) as exc:
            return False, f"Cannot reach Docker daemon: {exc}"
        return True, "Docker is available"

    def analyze(
        self,
        code: dict[str, str],
        config: dict[str, Any] | None = None,
    ) -> AnalyzerOutput:
        config = config or {}
        target_url: str | None = config.get("target_url")

        if target_url:
            return self._analyze_live(target_url)
        return self._analyze_static(code)

    def _analyze_live(self, target_url: str) -> AnalyzerOutput:
        available, msg = self.check_available()
        if not available:
            return AnalyzerOutput(error=f"ZAP unavailable: {msg}")

        cmd = [
            "docker",
            "run",
            "--rm",
            "-t",
            "ghcr.io/zaproxy/zaproxy:stable",
            "zap-baseline.py",
            "-t",
            target_url,
            "-J",
            "report.json",
        ]

        try:
            result = subprocess.run(  # noqa: S603
                cmd,
                capture_output=True,
                text=True,
                timeout=120,
                check=False,
            )
        except subprocess.TimeoutExpired:
            return AnalyzerOutput(
                error="ZAP scan timed out after 120 seconds",
            )
        except OSError as exc:
            return AnalyzerOutput(error=f"Failed to start ZAP: {exc}")

        return self._parse_zap_output(result)

    def _parse_zap_output(
        self,
        result: subprocess.CompletedProcess[str],
    ) -> AnalyzerOutput:
        findings: list[FindingData] = []
        raw: dict[str, Any] = {
            "stdout": result.stdout,
            "stderr": result.stderr,
            "returncode": result.returncode,
        }

        report: dict[str, Any] = {}
        for raw_line in result.stdout.splitlines():
            stripped = raw_line.strip()
            if stripped.startswith("{"):
                try:
                    report = json.loads(stripped)
                    break
                except json.JSONDecodeError:
                    continue

        if not report:
            with contextlib.suppress(json.JSONDecodeError, ValueError):
                report = json.loads(result.stdout)

        raw["report"] = report

        alert_counts: dict[str, int] = {
            "info": 0,
            "low": 0,
            "medium": 0,
            "high": 0,
        }

        for site in report.get("site", []):
            for alert in site.get("alerts", []):
                risk_code = int(alert.get("riskcode", 0))
                severity = ZAP_RISK_TO_SEVERITY.get(
                    risk_code,
                    "info",
                )
                alert_counts[severity] += 1

                instances = alert.get("instances", [])
                urls = [inst.get("uri", "") for inst in instances]

                findings.append(
                    FindingData(
                        severity=severity,
                        category="security",
                        title=alert.get("name", "ZAP Alert"),
                        description=alert.get("desc", ""),
                        suggestion=alert.get("solution", ""),
                        rule_id=str(alert.get("pluginid", "")),
                        confidence=_zap_confidence(
                            int(alert.get("confidence", 1)),
                        ),
                        tool_specific_data={
                            "risk_code": risk_code,
                            "cweid": alert.get("cweid", ""),
                            "wascid": alert.get("wascid", ""),
                            "reference": alert.get(
                                "reference",
                                "",
                            ),
                            "urls": urls,
                            "count": alert.get(
                                "count",
                                len(instances),
                            ),
                        },
                    ),
                )

        total_urls = sum(len(site.get("alerts", [])) for site in report.get("site", []))

        summary: dict[str, Any] = {
            "alert_counts": alert_counts,
            "total_alerts": len(findings),
            "total_urls_scanned": total_urls,
        }

        return AnalyzerOutput(
            findings=findings,
            summary=summary,
            raw_output=raw,
        )

    def _analyze_static(self, code: dict[str, str]) -> AnalyzerOutput:
        findings: list[FindingData] = []

        for file_key, content in code.items():
            lines = content.splitlines()
            for line_number, line_text in enumerate(lines, start=1):
                for entry in _STATIC_VULN_PATTERNS:
                    pat, title, desc, suggestion, sev, cat = entry
                    if re.search(pat, line_text):
                        findings.append(
                            FindingData(
                                severity=sev,
                                category=cat,
                                title=title,
                                description=desc,
                                suggestion=suggestion,
                                file_path=file_key,
                                line_number=line_number,
                                code_snippet=line_text.strip(),
                                rule_id=f"zap-static-{_slug(title)}",
                                confidence="medium",
                            ),
                        )

        counts = _empty_severity_counts()
        for f in findings:
            counts[f.severity] = counts.get(f.severity, 0) + 1

        summary: dict[str, Any] = {
            "mode": "static",
            "alert_counts": counts,
            "total_alerts": len(findings),
            "files_scanned": len(code),
        }

        return AnalyzerOutput(
            findings=findings,
            summary=summary,
            raw_output={"mode": "static"},
        )


class PortScanAnalyzer(BaseAnalyzer):
    """Port scanner — scans for open ports or analyzes code for exposed services."""

    name: ClassVar[str] = "port_scanner"
    analyzer_type: ClassVar[str] = "dynamic"
    display_name: ClassVar[str] = "Port Scanner"
    description: ClassVar[str] = (
        "Scans for open ports and identifies potentially dangerous exposed services"
    )

    def check_available(self) -> tuple[bool, str]:
        return True, "Available (uses Python built-in socket module)"

    def analyze(
        self,
        code: dict[str, str],
        config: dict[str, Any] | None = None,
    ) -> AnalyzerOutput:
        config = config or {}
        target_host: str | None = config.get("target_host")
        ports: list[int] = config.get("ports", DEFAULT_SCAN_PORTS)

        if target_host:
            return self._scan_host(target_host, ports)
        return self._analyze_static(code)

    def _scan_host(
        self,
        host: str,
        ports: list[int],
    ) -> AnalyzerOutput:
        findings: list[FindingData] = []
        open_ports: list[int] = []
        high_risk_ports: list[int] = []

        for port in ports:
            if self._is_port_open(host, port):
                open_ports.append(port)
                severity, port_desc = DANGEROUS_PORT_MAP.get(
                    port,
                    ("info", f"Port {port}"),
                )

                if severity in ("high", "critical"):
                    high_risk_ports.append(port)

                findings.append(
                    FindingData(
                        severity=severity,
                        category="security",
                        title=f"Open port {port} — {port_desc}",
                        description=(f"Port {port} is open on {host}: {port_desc}."),
                        suggestion=_port_suggestion(port),
                        rule_id=f"port-{port}",
                        confidence="high",
                        tool_specific_data={
                            "host": host,
                            "port": port,
                            "port_description": port_desc,
                        },
                    ),
                )

        summary: dict[str, Any] = {
            "target_host": host,
            "total_ports_scanned": len(ports),
            "open_ports_count": len(open_ports),
            "open_ports": open_ports,
            "high_risk_ports": high_risk_ports,
        }

        return AnalyzerOutput(
            findings=findings,
            summary=summary,
            raw_output={
                "host": host,
                "ports_scanned": ports,
                "open_ports": open_ports,
            },
        )

    @staticmethod
    def _is_port_open(
        host: str,
        port: int,
        timeout: float = 1.0,
    ) -> bool:
        try:
            with socket.socket(
                socket.AF_INET,
                socket.SOCK_STREAM,
            ) as sock:
                sock.settimeout(timeout)
                return sock.connect_ex((host, port)) == 0
        except OSError:
            return False

    def _analyze_static(self, code: dict[str, str]) -> AnalyzerOutput:
        findings: list[FindingData] = []

        for file_key, content in code.items():
            lines = content.splitlines()
            for line_number, line_text in enumerate(lines, start=1):
                for entry in _PORT_CODE_PATTERNS:
                    pat, title, desc, suggestion, sev = entry
                    if re.search(pat, line_text):
                        findings.append(
                            FindingData(
                                severity=sev,
                                category="security",
                                title=title,
                                description=desc,
                                suggestion=suggestion,
                                file_path=file_key,
                                line_number=line_number,
                                code_snippet=line_text.strip(),
                                rule_id=(f"portscan-static-{_slug(title)}"),
                                confidence="medium",
                            ),
                        )

        counts = _empty_severity_counts()
        for f in findings:
            counts[f.severity] = counts.get(f.severity, 0) + 1

        summary: dict[str, Any] = {
            "mode": "static",
            "alert_counts": counts,
            "total_alerts": len(findings),
            "files_scanned": len(code),
        }

        return AnalyzerOutput(
            findings=findings,
            summary=summary,
            raw_output={"mode": "static"},
        )


def _empty_severity_counts() -> dict[str, int]:
    return {
        "critical": 0,
        "high": 0,
        "medium": 0,
        "low": 0,
        "info": 0,
    }


def _zap_confidence(level: int) -> str:
    if level >= _ZAP_CONFIDENCE_HIGH:
        return "high"
    if level == _ZAP_CONFIDENCE_MEDIUM:
        return "medium"
    return "low"


def _slug(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


def _port_suggestion(port: int) -> str:
    suggestions: dict[int, str] = {
        21: "Disable FTP; use SFTP or SCP instead.",
        22: ("Restrict SSH access with key-based auth and firewall rules."),
        23: "Disable Telnet immediately; use SSH.",
        25: ("Restrict SMTP to trusted networks or use a managed email service."),
        53: "Ensure DNS is intentionally exposed and hardened.",
        80: "Consider redirecting HTTP to HTTPS.",
        443: "Ensure TLS certificates are valid and current.",
        3306: ("Do not expose MySQL publicly; use a firewall or SSH tunnel."),
        5432: ("Do not expose PostgreSQL publicly; use a firewall or SSH tunnel."),
        6379: ("Do not expose Redis publicly; enable auth and use a firewall."),
        8080: "Ensure this dev server is not in production.",
        8443: "Ensure this dev server is not in production.",
        27017: ("Do not expose MongoDB publicly; enable auth and use a firewall."),
    }
    return suggestions.get(
        port,
        "Review whether this port needs to be accessible.",
    )

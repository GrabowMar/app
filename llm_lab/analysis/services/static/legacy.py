"""Legacy static analyzers ported from the old container-based analysis stack."""

from __future__ import annotations

import contextlib
import json
import logging
import re
from pathlib import Path
from typing import TYPE_CHECKING
from typing import Any
from typing import ClassVar

from llm_lab.analysis.services.base import AnalyzerOutput
from llm_lab.analysis.services.base import BaseAnalyzer
from llm_lab.analysis.services.base import FindingData
from llm_lab.analysis.services.base import check_cli
from llm_lab.analysis.services.base import materialize_analysis_project
from llm_lab.analysis.services.base import run_subprocess

if TYPE_CHECKING:
    from llm_lab.analysis.services.cancellation import CancellationToken

logger = logging.getLogger(__name__)

_REQ_LOCATIONS = (
    "requirements.txt",
    "backend/requirements.txt",
    "api/requirements.txt",
    "server/requirements.txt",
)
_PKG_JSON_GLOB = "package.json"
_SEMGREP_SEVERITY_MAP = {
    "ERROR": "high",
    "WARNING": "medium",
    "INFO": "low",
}
_RUFF_PREFIX_SEVERITY_MAP = {
    "F": "high",
    "S": "high",
    "B": "high",
    "E": "medium",
    "W": "medium",
    "C": "medium",
    "A": "medium",
    "I": "low",
    "N": "low",
    "D": "low",
    "UP": "low",
}
_RADON_RANK_SEVERITY = {
    "A": "low",
    "B": "low",
    "C": "medium",
    "D": "medium",
    "E": "high",
    "F": "high",
}


def _safe_int(value: object, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _rel_path(path: str | Path, root: Path) -> str:
    candidate = Path(path)
    with contextlib.suppress(ValueError):
        return str(candidate.resolve().relative_to(root.resolve()))
    return str(candidate)


def _python_target(root: Path) -> Path | None:
    for candidate in (root / "backend", root / "api", root / "server", root):
        if candidate.exists() and any(candidate.rglob("*.py")):
            return candidate
    return None


def _find_requirements_file(root: Path) -> Path | None:
    for location in _REQ_LOCATIONS:
        candidate = root / location
        if candidate.is_file():
            return candidate
    return None


def _find_package_dirs(root: Path) -> list[Path]:
    return sorted(
        {
            package_json.parent
            for package_json in root.rglob(_PKG_JSON_GLOB)
            if "node_modules" not in package_json.parts
        },
    )


def _extract_json_object(text: str) -> dict[str, Any] | None:
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end <= start:
        return None
    try:
        parsed = json.loads(text[start : end + 1])
    except json.JSONDecodeError:
        return None
    return parsed if isinstance(parsed, dict) else None


def _severity_from_cvss(score: float | None) -> str:
    if score is None:
        return "high"
    if score >= 9:
        return "critical"
    if score >= 7:
        return "high"
    if score >= 4:
        return "medium"
    return "low"


class SemgrepAnalyzer(BaseAnalyzer):
    name: ClassVar[str] = "semgrep"
    analyzer_type: ClassVar[str] = "static"
    display_name: ClassVar[str] = "Semgrep Security Scanner"
    description: ClassVar[str] = "Multi-language static analysis security scanner"
    default_timeout: ClassVar[int] = 90
    default_config: ClassVar[dict[str, Any]] = {
        "config": "auto",
        "exclude": [],
    }

    def check_available(self) -> tuple[bool, str]:
        return check_cli(["semgrep", "--version"], tool_name="Semgrep")

    def analyze(
        self,
        code: dict[str, str],
        config: dict[str, Any] | None = None,
        *,
        cancel: CancellationToken | None = None,
    ) -> AnalyzerOutput:
        available, message = self.get_availability()
        if not available:
            return AnalyzerOutput(error=message)
        merged = {**self.default_config, **(config or {})}
        with materialize_analysis_project(code, config=merged) as root:
            result = run_subprocess(
                [
                    "semgrep",
                    "scan",
                    "--json",
                    "--config",
                    str(merged["config"]),
                    *[
                        value
                        for item in merged.get("exclude", [])
                        for value in ("--exclude", str(item))
                    ],
                    str(root),
                ],
                timeout=int(merged.get("timeout", self.default_timeout)),
                cancel=cancel,
                cwd=root,
            )
            if result is None:
                if cancel and cancel.is_cancelled():
                    return AnalyzerOutput(error="Analysis cancelled")
                return AnalyzerOutput(error="Semgrep analysis timed out")
            if result.returncode not in {0, 1}:
                return AnalyzerOutput(error=f"Semgrep failed: {result.stderr[:500]}")
            try:
                data = json.loads(result.stdout or "{}")
            except json.JSONDecodeError:
                return AnalyzerOutput(error="Failed to parse Semgrep output")

            findings: list[FindingData] = []
            for issue in data.get("results", []):
                extra = issue.get("extra", {})
                start = issue.get("start", {})
                severity = _SEMGREP_SEVERITY_MAP.get(str(extra.get("severity", "WARNING")).upper(), "medium")
                findings.append(
                    FindingData(
                        severity=severity,
                        category="security",
                        title=extra.get("message", issue.get("check_id", "Semgrep finding")),
                        description=extra.get("message", ""),
                        suggestion="Review the Semgrep rule guidance for this finding.",
                        file_path=_rel_path(issue.get("path", ""), root),
                        line_number=_safe_int(start.get("line")) or None,
                        column_number=_safe_int(start.get("col")) or None,
                        code_snippet=extra.get("lines", ""),
                        rule_id=issue.get("check_id", ""),
                        confidence="high",
                        tool_specific_data={"metadata": extra.get("metadata", {})},
                    ),
                )

            return AnalyzerOutput(
                findings=findings,
                summary={
                    "total_issues": len(findings),
                    "errors": data.get("errors", []),
                    "config": merged["config"],
                },
                raw_output=data,
            )


class MyPyAnalyzer(BaseAnalyzer):
    name: ClassVar[str] = "mypy"
    analyzer_type: ClassVar[str] = "static"
    display_name: ClassVar[str] = "MyPy Type Checker"
    description: ClassVar[str] = "Static type checker for Python"
    default_timeout: ClassVar[int] = 90
    default_config: ClassVar[dict[str, Any]] = {
        "strict": False,
        "ignore_missing_imports": True,
    }

    def check_available(self) -> tuple[bool, str]:
        return check_cli(["mypy", "--version"], tool_name="MyPy")

    def analyze(
        self,
        code: dict[str, str],
        config: dict[str, Any] | None = None,
        *,
        cancel: CancellationToken | None = None,
    ) -> AnalyzerOutput:
        available, message = self.get_availability()
        if not available:
            return AnalyzerOutput(error=message)
        merged = {**self.default_config, **(config or {})}
        with materialize_analysis_project(code, config=merged) as root:
            python_root = _python_target(root)
            if python_root is None:
                return AnalyzerOutput(summary={"message": "No Python code to analyze"})

            cmd = [
                "mypy",
                "--show-column-numbers",
                "--hide-error-context",
                "--no-error-summary",
            ]
            if merged.get("strict"):
                cmd.append("--strict")
            if merged.get("ignore_missing_imports", True):
                cmd.append("--ignore-missing-imports")
            cmd.append(str(python_root))

            result = run_subprocess(
                cmd,
                timeout=int(merged.get("timeout", self.default_timeout)),
                cancel=cancel,
                cwd=root,
            )
            if result is None:
                if cancel and cancel.is_cancelled():
                    return AnalyzerOutput(error="Analysis cancelled")
                return AnalyzerOutput(error="MyPy analysis timed out")
            if result.returncode not in {0, 1}:
                return AnalyzerOutput(error=f"MyPy failed: {result.stderr[:500]}")

            findings: list[FindingData] = []
            pattern = re.compile(
                r"^(?P<file>.+?):(?P<line>\d+):(?P<column>\d+): "
                r"(?P<kind>error|warning|note): (?P<message>.*?)(?:\s+\[(?P<code>[^\]]+)\])?$",
            )
            for line in result.stdout.splitlines():
                match = pattern.match(line.strip())
                if not match:
                    continue
                kind = match.group("kind")
                severity = "high" if kind == "error" else ("medium" if kind == "warning" else "low")
                findings.append(
                    FindingData(
                        severity=severity,
                        category="quality",
                        title=match.group("message"),
                        description=match.group("message"),
                        suggestion="Fix the reported type mismatch or add the required type annotations.",
                        file_path=_rel_path(match.group("file"), root),
                        line_number=_safe_int(match.group("line")) or None,
                        column_number=_safe_int(match.group("column")) or None,
                        rule_id=match.group("code") or "type-check",
                        confidence="high",
                    ),
                )

            return AnalyzerOutput(
                findings=findings,
                summary={"total_issues": len(findings)},
                raw_output={"stdout": result.stdout, "stderr": result.stderr},
            )


class VultureAnalyzer(BaseAnalyzer):
    name: ClassVar[str] = "vulture"
    analyzer_type: ClassVar[str] = "static"
    display_name: ClassVar[str] = "Vulture Dead Code Detector"
    description: ClassVar[str] = "Finds unused code in Python programs"
    default_timeout: ClassVar[int] = 60
    default_config: ClassVar[dict[str, Any]] = {
        "min_confidence": 80,
        "sort_by_size": False,
    }

    def check_available(self) -> tuple[bool, str]:
        return check_cli(["vulture", "--version"], tool_name="Vulture")

    def analyze(
        self,
        code: dict[str, str],
        config: dict[str, Any] | None = None,
        *,
        cancel: CancellationToken | None = None,
    ) -> AnalyzerOutput:
        available, message = self.get_availability()
        if not available:
            return AnalyzerOutput(error=message)
        merged = {**self.default_config, **(config or {})}
        with materialize_analysis_project(code, config=merged) as root:
            python_root = _python_target(root)
            if python_root is None:
                return AnalyzerOutput(summary={"message": "No Python code to analyze"})

            cmd = [
                "vulture",
                str(python_root),
                "--min-confidence",
                str(merged["min_confidence"]),
            ]
            if merged.get("sort_by_size"):
                cmd.append("--sort-by-size")
            result = run_subprocess(
                cmd,
                timeout=int(merged.get("timeout", self.default_timeout)),
                cancel=cancel,
                cwd=root,
            )
            if result is None:
                if cancel and cancel.is_cancelled():
                    return AnalyzerOutput(error="Analysis cancelled")
                return AnalyzerOutput(error="Vulture analysis timed out")
            if result.returncode not in {0, 1, 3}:
                return AnalyzerOutput(error=f"Vulture failed: {result.stderr[:500]}")

            findings: list[FindingData] = []
            pattern = re.compile(
                r"^(?P<file>.+?):(?P<line>\d+): "
                r"(?P<message>.*?)(?: \((?P<confidence>\d+)% confidence\))?$",
            )
            for line in result.stdout.splitlines():
                match = pattern.match(line.strip())
                if not match:
                    continue
                confidence = _safe_int(match.group("confidence"), default=60)
                severity = "medium" if confidence >= 80 else "low"
                findings.append(
                    FindingData(
                        severity=severity,
                        category="quality",
                        title="Potential dead code",
                        description=match.group("message"),
                        suggestion="Remove the unused code or reference it from live execution paths.",
                        file_path=_rel_path(match.group("file"), root),
                        line_number=_safe_int(match.group("line")) or None,
                        rule_id="dead-code",
                        confidence="medium" if confidence >= 80 else "low",
                        tool_specific_data={"confidence_percent": confidence},
                    ),
                )

            return AnalyzerOutput(
                findings=findings,
                summary={"total_issues": len(findings)},
                raw_output={"stdout": result.stdout, "stderr": result.stderr},
            )


class RuffAnalyzer(BaseAnalyzer):
    name: ClassVar[str] = "ruff"
    analyzer_type: ClassVar[str] = "static"
    display_name: ClassVar[str] = "Ruff Fast Linter"
    description: ClassVar[str] = "Fast Python linter with quality and security checks"
    default_timeout: ClassVar[int] = 60
    default_config: ClassVar[dict[str, Any]] = {
        "select": [],
        "ignore": [],
        "target_version": "py313",
    }

    def check_available(self) -> tuple[bool, str]:
        return check_cli(["ruff", "--version"], tool_name="Ruff")

    def analyze(  # noqa: PLR0911
        self,
        code: dict[str, str],
        config: dict[str, Any] | None = None,
        *,
        cancel: CancellationToken | None = None,
    ) -> AnalyzerOutput:
        available, message = self.get_availability()
        if not available:
            return AnalyzerOutput(error=message)
        merged = {**self.default_config, **(config or {})}
        with materialize_analysis_project(code, config=merged) as root:
            python_root = _python_target(root)
            if python_root is None:
                return AnalyzerOutput(summary={"message": "No Python code to analyze"})

            cmd = [
                "ruff",
                "check",
                "--output-format",
                "json",
                "--target-version",
                str(merged["target_version"]),
            ]
            if merged.get("select"):
                cmd.extend(["--select", ",".join(merged["select"])])
            if merged.get("ignore"):
                cmd.extend(["--ignore", ",".join(merged["ignore"])])
            cmd.append(str(python_root))

            result = run_subprocess(
                cmd,
                timeout=int(merged.get("timeout", self.default_timeout)),
                cancel=cancel,
                cwd=root,
            )
            if result is None:
                if cancel and cancel.is_cancelled():
                    return AnalyzerOutput(error="Analysis cancelled")
                return AnalyzerOutput(error="Ruff analysis timed out")
            if result.returncode not in {0, 1}:
                return AnalyzerOutput(error=f"Ruff failed: {result.stderr[:500]}")

            try:
                data = json.loads(result.stdout or "[]")
            except json.JSONDecodeError:
                return AnalyzerOutput(error="Failed to parse Ruff output")

            findings: list[FindingData] = []
            for issue in data:
                rule_id = issue.get("code", "")
                prefix = "UP" if rule_id.startswith("UP") else (rule_id[:1] if rule_id else "E")
                severity = _RUFF_PREFIX_SEVERITY_MAP.get(prefix, "medium")
                location = issue.get("location", {})
                category = "security" if rule_id.startswith("S") else "quality"
                findings.append(
                    FindingData(
                        severity=severity,
                        category=category,
                        title=issue.get("message", "Ruff finding"),
                        description=issue.get("message", ""),
                        suggestion="Apply Ruff's suggestion or update the code to satisfy the rule.",
                        file_path=_rel_path(issue.get("filename", ""), root),
                        line_number=_safe_int(location.get("row")) or None,
                        column_number=_safe_int(location.get("column")) or None,
                        rule_id=rule_id,
                        confidence="high",
                        tool_specific_data={"fix_available": issue.get("fix") is not None},
                    ),
                )

            return AnalyzerOutput(
                findings=findings,
                summary={"total_issues": len(findings)},
                raw_output=data,
            )


class SafetyAnalyzer(BaseAnalyzer):
    name: ClassVar[str] = "safety"
    analyzer_type: ClassVar[str] = "static"
    display_name: ClassVar[str] = "Safety Dependency Scanner"
    description: ClassVar[str] = "Python dependency vulnerability scanner"
    default_timeout: ClassVar[int] = 60

    def check_available(self) -> tuple[bool, str]:
        return check_cli(["safety", "--version"], tool_name="Safety")

    def analyze(  # noqa: PLR0911
        self,
        code: dict[str, str],
        config: dict[str, Any] | None = None,
        *,
        cancel: CancellationToken | None = None,
    ) -> AnalyzerOutput:
        available, message = self.get_availability()
        if not available:
            return AnalyzerOutput(error=message)
        merged = config or {}
        with materialize_analysis_project(code, config=merged) as root:
            requirements_file = _find_requirements_file(root)
            if requirements_file is None:
                return AnalyzerOutput(summary={"message": "No requirements.txt file found"})

            result = run_subprocess(
                ["safety", "check", "-r", str(requirements_file), "--output", "json"],
                timeout=int(merged.get("timeout", self.default_timeout)),
                cancel=cancel,
                cwd=root,
            )
            if result is None:
                if cancel and cancel.is_cancelled():
                    return AnalyzerOutput(error="Analysis cancelled")
                return AnalyzerOutput(error="Safety scan timed out")
            if result.returncode not in {0, 1, 64}:
                return AnalyzerOutput(error=f"Safety failed: {result.stderr[:500]}")

            data = _extract_json_object(result.stdout or "")
            if data is None:
                return AnalyzerOutput(
                    error="Failed to parse Safety output",
                    raw_output={"stdout": result.stdout, "stderr": result.stderr},
                )

            findings: list[FindingData] = []
            for vuln in data.get("vulnerabilities", []):
                cvss = vuln.get("severity", {}).get("cvssv3", {})
                score = cvss.get("base_score") if isinstance(cvss, dict) else None
                severity = _severity_from_cvss(score)
                findings.append(
                    FindingData(
                        severity=severity,
                        category="security",
                        title=f"{vuln.get('package_name', 'dependency')} vulnerability",
                        description=vuln.get("advisory", ""),
                        suggestion=(
                            "Upgrade to one of the fixed versions: "
                            + ", ".join(vuln.get("fixed_versions", []))
                        ).strip(),
                        file_path=_rel_path(requirements_file, root),
                        rule_id=vuln.get("CVE") or vuln.get("vulnerability_id", ""),
                        confidence="high",
                        tool_specific_data={
                            "package": vuln.get("package_name"),
                            "installed_version": vuln.get("analyzed_version"),
                            "fixed_versions": vuln.get("fixed_versions", []),
                            "more_info_url": vuln.get("more_info_url", ""),
                        },
                    ),
                )

            return AnalyzerOutput(
                findings=findings,
                summary={
                    "total_issues": len(findings),
                    "scanned_packages": len(data.get("scanned_packages", [])),
                },
                raw_output=data,
            )


class PipAuditAnalyzer(BaseAnalyzer):
    name: ClassVar[str] = "pip-audit"
    analyzer_type: ClassVar[str] = "static"
    display_name: ClassVar[str] = "pip-audit CVE Scanner"
    description: ClassVar[str] = "Python dependency CVE and vulnerability scanner"
    default_timeout: ClassVar[int] = 90

    def check_available(self) -> tuple[bool, str]:
        return check_cli(["pip-audit", "--version"], tool_name="pip-audit")

    def analyze(  # noqa: PLR0911
        self,
        code: dict[str, str],
        config: dict[str, Any] | None = None,
        *,
        cancel: CancellationToken | None = None,
    ) -> AnalyzerOutput:
        available, message = self.get_availability()
        if not available:
            return AnalyzerOutput(error=message)
        merged = config or {}
        with materialize_analysis_project(code, config=merged) as root:
            requirements_file = _find_requirements_file(root)
            if requirements_file is None:
                return AnalyzerOutput(summary={"message": "No requirements.txt file found"})

            result = run_subprocess(
                ["pip-audit", "--format", "json", "--requirement", str(requirements_file)],
                timeout=int(merged.get("timeout", self.default_timeout)),
                cancel=cancel,
                cwd=root,
            )
            if result is None:
                if cancel and cancel.is_cancelled():
                    return AnalyzerOutput(error="Analysis cancelled")
                return AnalyzerOutput(error="pip-audit timed out")
            if result.returncode not in {0, 1}:
                return AnalyzerOutput(error=f"pip-audit failed: {result.stderr[:500]}")

            try:
                data = json.loads(result.stdout or "{}")
            except json.JSONDecodeError:
                return AnalyzerOutput(error="Failed to parse pip-audit output")

            findings: list[FindingData] = []
            for dependency in data.get("dependencies", []):
                for vuln in dependency.get("vulns", []):
                    findings.append(
                        FindingData(
                            severity="high",
                            category="security",
                            title=f"{dependency.get('name', 'dependency')} vulnerability",
                            description=vuln.get("description", ""),
                            suggestion=(
                                "Upgrade to one of the fixed versions: "
                                + ", ".join(vuln.get("fix_versions", []))
                            ).strip(),
                            file_path=_rel_path(requirements_file, root),
                            rule_id=vuln.get("id", ""),
                            confidence="high",
                            tool_specific_data={
                                "package": dependency.get("name"),
                                "installed_version": dependency.get("version"),
                                "aliases": vuln.get("aliases", []),
                            },
                        ),
                    )

            return AnalyzerOutput(
                findings=findings,
                summary={"total_issues": len(findings)},
                raw_output=data,
            )


class RadonAnalyzer(BaseAnalyzer):
    name: ClassVar[str] = "radon"
    analyzer_type: ClassVar[str] = "static"
    display_name: ClassVar[str] = "Radon Complexity"
    description: ClassVar[str] = "Python cyclomatic complexity calculator"
    default_timeout: ClassVar[int] = 60
    default_config: ClassVar[dict[str, Any]] = {
        "min_complexity": "B",
    }

    def check_available(self) -> tuple[bool, str]:
        return check_cli(["radon", "--help"], tool_name="Radon")

    def analyze(  # noqa: PLR0911
        self,
        code: dict[str, str],
        config: dict[str, Any] | None = None,
        *,
        cancel: CancellationToken | None = None,
    ) -> AnalyzerOutput:
        available, message = self.get_availability()
        if not available:
            return AnalyzerOutput(error=message)
        merged = {**self.default_config, **(config or {})}
        with materialize_analysis_project(code, config=merged) as root:
            python_root = _python_target(root)
            if python_root is None:
                return AnalyzerOutput(summary={"message": "No Python code to analyze"})

            result = run_subprocess(
                ["radon", "cc", "-j", "-n", str(merged["min_complexity"]), str(python_root)],
                timeout=int(merged.get("timeout", self.default_timeout)),
                cancel=cancel,
                cwd=root,
            )
            if result is None:
                if cancel and cancel.is_cancelled():
                    return AnalyzerOutput(error="Analysis cancelled")
                return AnalyzerOutput(error="Radon analysis timed out")
            if result.returncode not in {0}:
                return AnalyzerOutput(error=f"Radon failed: {result.stderr[:500]}")

            try:
                data = json.loads(result.stdout or "{}")
            except json.JSONDecodeError:
                return AnalyzerOutput(error="Failed to parse Radon output")

            findings: list[FindingData] = []
            for file_path, blocks in data.items():
                if not isinstance(blocks, list):
                    continue
                for block in blocks:
                    rank = str(block.get("rank", "A"))
                    severity = _RADON_RANK_SEVERITY.get(rank, "low")
                    findings.append(
                        FindingData(
                            severity=severity,
                            category="quality",
                            title=f"High complexity in {block.get('name', 'code block')}",
                            description=(
                                f"{block.get('type', 'block')} has cyclomatic complexity "
                                f"{block.get('complexity', 0)} (rank {rank})."
                            ),
                            suggestion="Simplify the control flow or extract smaller helper functions.",
                            file_path=_rel_path(file_path, root),
                            line_number=_safe_int(block.get("lineno")) or None,
                            column_number=_safe_int(block.get("col_offset")) or None,
                            rule_id="cyclomatic-complexity",
                            confidence="high",
                            tool_specific_data={"rank": rank, "complexity": block.get("complexity")},
                        ),
                    )

            return AnalyzerOutput(
                findings=findings,
                summary={"total_issues": len(findings)},
                raw_output=data,
            )


class DetectSecretsAnalyzer(BaseAnalyzer):
    name: ClassVar[str] = "detect-secrets"
    analyzer_type: ClassVar[str] = "static"
    display_name: ClassVar[str] = "Detect Secrets"
    description: ClassVar[str] = "Detects potential hard-coded credentials and secrets"
    default_timeout: ClassVar[int] = 60

    def check_available(self) -> tuple[bool, str]:
        return check_cli(["detect-secrets", "--version"], tool_name="detect-secrets")

    def analyze(
        self,
        code: dict[str, str],
        config: dict[str, Any] | None = None,
        *,
        cancel: CancellationToken | None = None,
    ) -> AnalyzerOutput:
        available, message = self.get_availability()
        if not available:
            return AnalyzerOutput(error=message)
        merged = config or {}
        with materialize_analysis_project(code, config=merged) as root:
            result = run_subprocess(
                ["detect-secrets", "scan", "--all-files", str(root)],
                timeout=int(merged.get("timeout", self.default_timeout)),
                cancel=cancel,
                cwd=root,
            )
            if result is None:
                if cancel and cancel.is_cancelled():
                    return AnalyzerOutput(error="Analysis cancelled")
                return AnalyzerOutput(error="detect-secrets timed out")
            if result.returncode not in {0}:
                return AnalyzerOutput(error=f"detect-secrets failed: {result.stderr[:500]}")

            try:
                data = json.loads(result.stdout or "{}")
            except json.JSONDecodeError:
                return AnalyzerOutput(error="Failed to parse detect-secrets output")

            findings: list[FindingData] = []
            for file_path, secrets in (data.get("results") or {}).items():
                for secret in secrets:
                    findings.append(
                        FindingData(
                            severity="high",
                            category="security",
                            title=f"Potential secret detected ({secret.get('type', 'unknown')})",
                            description="Potential secret or credential committed in source code.",
                            suggestion="Move the secret into environment variables or a secrets manager.",
                            file_path=_rel_path(file_path, root),
                            line_number=_safe_int(secret.get("line_number")) or None,
                            rule_id="secret-detection",
                            confidence="high" if secret.get("is_verified") else "medium",
                            tool_specific_data={
                                "secret_type": secret.get("type", ""),
                                "is_verified": bool(secret.get("is_verified")),
                            },
                        ),
                    )

            return AnalyzerOutput(
                findings=findings,
                summary={"total_issues": len(findings)},
                raw_output=data,
            )


class NpmAuditAnalyzer(BaseAnalyzer):
    name: ClassVar[str] = "npm-audit"
    analyzer_type: ClassVar[str] = "static"
    display_name: ClassVar[str] = "npm-audit CVE Scanner"
    description: ClassVar[str] = "JavaScript/Node.js dependency CVE and vulnerability scanner"
    default_timeout: ClassVar[int] = 90

    def check_available(self) -> tuple[bool, str]:
        return check_cli(["npm", "--version"], tool_name="npm")

    def analyze(
        self,
        code: dict[str, str],
        config: dict[str, Any] | None = None,
        *,
        cancel: CancellationToken | None = None,
    ) -> AnalyzerOutput:
        available, message = self.get_availability()
        if not available:
            return AnalyzerOutput(error=message)
        merged = config or {}
        findings: list[FindingData] = []
        raw_runs: list[dict[str, Any]] = []

        with materialize_analysis_project(code, config=merged) as root:
            package_dirs = _find_package_dirs(root)
            if not package_dirs:
                return AnalyzerOutput(summary={"message": "No package.json file found"})

            for package_dir in package_dirs:
                lockfile = package_dir / "package-lock.json"
                if not lockfile.exists():
                    generated = run_subprocess(
                        ["npm", "install", "--package-lock-only", "--ignore-scripts", "--no-fund", "--no-audit"],
                        timeout=120,
                        cancel=cancel,
                        cwd=package_dir,
                    )
                    if generated is None:
                        return AnalyzerOutput(error="npm install --package-lock-only timed out")
                    if generated.returncode != 0:
                        raw_runs.append(
                            {
                                "package_dir": str(package_dir),
                                "lockfile_error": generated.stderr,
                            },
                        )
                        continue

                result = run_subprocess(
                    ["npm", "audit", "--json"],
                    timeout=int(merged.get("timeout", self.default_timeout)),
                    cancel=cancel,
                    cwd=package_dir,
                )
                if result is None:
                    if cancel and cancel.is_cancelled():
                        return AnalyzerOutput(error="Analysis cancelled")
                    return AnalyzerOutput(error="npm audit timed out")
                if result.returncode not in {0, 1}:
                    raw_runs.append({"package_dir": str(package_dir), "stderr": result.stderr})
                    continue

                try:
                    data = json.loads(result.stdout or "{}")
                except json.JSONDecodeError:
                    raw_runs.append(
                        {
                            "package_dir": str(package_dir),
                            "stdout": result.stdout,
                            "stderr": result.stderr,
                        },
                    )
                    continue

                raw_runs.append({"package_dir": str(package_dir), "report": data})
                for package_name, vulnerability in (data.get("vulnerabilities") or {}).items():
                    if not isinstance(vulnerability, dict):
                        continue
                    raw_severity = str(vulnerability.get("severity", "info")).lower()
                    severity = (
                        "critical" if raw_severity == "critical"
                        else "high" if raw_severity == "high"
                        else "medium" if raw_severity in {"moderate", "medium"}
                        else "low" if raw_severity == "low"
                        else "info"
                    )
                    findings.append(
                        FindingData(
                            severity=severity,
                            category="security",
                            title=f"{package_name} vulnerability",
                            description=vulnerability.get("title", vulnerability.get("overview", "")),
                            suggestion="Upgrade the package to a non-vulnerable version.",
                            file_path=_rel_path(package_dir / "package.json", root),
                            rule_id=package_name,
                            confidence="high",
                            tool_specific_data={
                                "severity": raw_severity,
                                "via": vulnerability.get("via", []),
                                "fix_available": vulnerability.get("fixAvailable"),
                            },
                        ),
                    )

        return AnalyzerOutput(
            findings=findings,
            summary={"total_issues": len(findings), "projects_scanned": len(raw_runs)},
            raw_output={"runs": raw_runs},
        )

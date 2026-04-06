"""Static analysis tools: Bandit, ESLint, and Pylint."""

from __future__ import annotations

import json
import logging
import subprocess
import tempfile
from pathlib import Path
from typing import Any
from typing import ClassVar

from llm_lab.analysis.services.base import AnalyzerOutput
from llm_lab.analysis.services.base import BaseAnalyzer
from llm_lab.analysis.services.base import FindingData

logger = logging.getLogger(__name__)

PYTHON_EXTENSIONS = {".py", ".pyw"}
JS_TS_EXTENSIONS = {".js", ".jsx", ".ts", ".tsx", ".mjs", ".cjs"}


def _extract_code(code: dict[str, str], key: str, extensions: set[str]) -> str:
    """Extract code from a code dict that may use semantic keys or filenames.

    Tries the semantic key first (e.g. "backend", "frontend"), then falls back
    to concatenating all values whose keys look like files with matching extensions.
    """
    if key in code and code[key].strip():
        return code[key]
    # Fall back: collect all entries whose key ends with a matching extension
    parts: list[str] = []
    for filename, content in code.items():
        if not content or not content.strip():
            continue
        ext = Path(filename).suffix.lower() if "." in filename else ""
        if ext in extensions:
            parts.append(f"# --- {filename} ---\n{content}")
    return "\n\n".join(parts)


BANDIT_SEVERITY_MAP: dict[str, str] = {
    "HIGH": "high",
    "MEDIUM": "medium",
    "LOW": "low",
}

BANDIT_CONFIDENCE_MAP: dict[str, str] = {
    "HIGH": "high",
    "MEDIUM": "medium",
    "LOW": "low",
}

ESLINT_SEVERITY_MAP: dict[int, str] = {
    1: "low",
    2: "high",
}

PYLINT_SEVERITY_MAP: dict[str, str] = {
    "C": "info",
    "R": "low",
    "W": "medium",
    "E": "high",
    "F": "critical",
}

PYLINT_CATEGORY_MAP: dict[str, str] = {
    "C": "style",
    "R": "quality",
    "W": "quality",
    "E": "quality",
    "F": "quality",
}


class BanditAnalyzer(BaseAnalyzer):
    """Runs Bandit security scanner on Python code."""

    name: ClassVar[str] = "bandit"
    analyzer_type: ClassVar[str] = "static"
    display_name: ClassVar[str] = "Bandit Security Scanner"
    description: ClassVar[str] = "Finds common security issues in Python code."

    def check_available(self) -> tuple[bool, str]:
        try:
            result = subprocess.run(
                ["bandit", "--version"],  # noqa: S607
                capture_output=True,
                text=True,
                timeout=10,
                check=False,
            )
        except FileNotFoundError:
            return False, "Bandit is not installed"
        except subprocess.TimeoutExpired:
            return False, "Bandit version check timed out"
        else:
            if result.returncode == 0:
                version = result.stdout.strip().split("\n")[0]
                return True, f"Bandit {version}"
            return False, "Bandit is not installed"

    def analyze(
        self,
        code: dict[str, str],
        config: dict[str, Any] | None = None,
    ) -> AnalyzerOutput:
        source = _extract_code(code, "backend", PYTHON_EXTENSIONS)
        if not source.strip():
            return AnalyzerOutput(
                summary={"message": "No Python code to analyze"},
            )

        available, _message = self.check_available()
        if not available:
            return AnalyzerOutput(error="Bandit is not installed")

        tmp_path: str | None = None
        try:
            with tempfile.NamedTemporaryFile(
                mode="w",
                suffix=".py",
                delete=False,
            ) as tmp:
                tmp.write(source)
                tmp_path = tmp.name

            result = subprocess.run(  # noqa: S603
                ["bandit", "-f", "json", "-r", tmp_path],  # noqa: S607
                capture_output=True,
                text=True,
                timeout=60,
                check=False,
            )

            return self._parse_output(result)
        except subprocess.TimeoutExpired:
            logger.exception("Bandit analysis timed out")
            return AnalyzerOutput(error="Bandit analysis timed out")
        except Exception:
            logger.exception("Bandit analysis failed")
            return AnalyzerOutput(error="Bandit analysis failed unexpectedly")
        finally:
            if tmp_path:
                Path(tmp_path).unlink(missing_ok=True)

    def _parse_output(
        self,
        result: subprocess.CompletedProcess[str],
    ) -> AnalyzerOutput:
        try:
            data = json.loads(result.stdout)
        except (json.JSONDecodeError, TypeError):
            logger.exception("Failed to parse Bandit JSON output")
            return AnalyzerOutput(
                error="Failed to parse Bandit output",
                raw_output={
                    "stdout": result.stdout,
                    "stderr": result.stderr,
                },
            )

        findings: list[FindingData] = []
        for issue in data.get("results", []):
            sev = issue.get("issue_severity", "")
            conf = issue.get("issue_confidence", "")
            test_id = issue.get("test_id", "")
            findings.append(
                FindingData(
                    severity=BANDIT_SEVERITY_MAP.get(sev, "medium"),
                    category="security",
                    title=issue.get("issue_text", "Security issue"),
                    description=issue.get("issue_text", ""),
                    suggestion=f"See Bandit docs for {test_id or 'this issue'}.",
                    file_path=issue.get("filename", ""),
                    line_number=issue.get("line_number"),
                    column_number=issue.get("col_offset"),
                    code_snippet=issue.get("code", ""),
                    rule_id=test_id,
                    confidence=BANDIT_CONFIDENCE_MAP.get(conf, "medium"),
                    tool_specific_data={
                        "test_name": issue.get("test_name", ""),
                        "line_range": issue.get("line_range", []),
                        "more_info": issue.get("more_info", ""),
                    },
                ),
            )

        severity_counts = {"critical": 0, "high": 0, "medium": 0, "low": 0, "info": 0}
        confidence_counts = {"high": 0, "medium": 0, "low": 0}
        for f in findings:
            if f.severity in severity_counts:
                severity_counts[f.severity] += 1
            if f.confidence in confidence_counts:
                confidence_counts[f.confidence] += 1

        return AnalyzerOutput(
            findings=findings,
            summary={
                "total_issues": len(findings),
                "by_severity": severity_counts,
                "by_confidence": confidence_counts,
            },
            raw_output=data,
        )


class ESLintAnalyzer(BaseAnalyzer):
    """Runs ESLint on JavaScript/TypeScript code."""

    name: ClassVar[str] = "eslint"
    analyzer_type: ClassVar[str] = "static"
    display_name: ClassVar[str] = "ESLint Code Analyzer"
    description: ClassVar[str] = "Finds problems in JavaScript and TypeScript code."

    def check_available(self) -> tuple[bool, str]:
        try:
            result = subprocess.run(
                ["npx", "eslint", "--version"],  # noqa: S607
                capture_output=True,
                text=True,
                timeout=30,
                check=False,
            )
        except FileNotFoundError:
            return False, "ESLint is not installed"
        except subprocess.TimeoutExpired:
            return False, "ESLint version check timed out"
        else:
            if result.returncode == 0:
                version = result.stdout.strip()
                return True, f"ESLint {version}"
            return False, "ESLint is not installed"

    def analyze(
        self,
        code: dict[str, str],
        config: dict[str, Any] | None = None,
    ) -> AnalyzerOutput:
        source = _extract_code(code, "frontend", JS_TS_EXTENSIONS)
        if not source.strip():
            return AnalyzerOutput(
                summary={
                    "message": "No JavaScript/TypeScript code to analyze",
                },
            )

        available, _message = self.check_available()
        if not available:
            return AnalyzerOutput(error="ESLint is not installed")

        tmp_path: str | None = None
        try:
            with tempfile.NamedTemporaryFile(
                mode="w",
                suffix=".js",
                delete=False,
            ) as tmp:
                tmp.write(source)
                tmp_path = tmp.name

            rules = json.dumps(
                {
                    "no-unused-vars": "warn",
                    "no-undef": "error",
                    "no-eval": "error",
                    "no-implied-eval": "error",
                    "no-new-func": "error",
                },
            )
            result = subprocess.run(  # noqa: S603
                [  # noqa: S607
                    "npx",
                    "eslint",
                    "--format",
                    "json",
                    tmp_path,
                    "--no-eslintrc",
                    "--rule",
                    rules,
                ],
                capture_output=True,
                text=True,
                timeout=60,
                check=False,
            )

            return self._parse_output(result)
        except subprocess.TimeoutExpired:
            logger.exception("ESLint analysis timed out")
            return AnalyzerOutput(error="ESLint analysis timed out")
        except Exception:
            logger.exception("ESLint analysis failed")
            return AnalyzerOutput(error="ESLint analysis failed unexpectedly")
        finally:
            if tmp_path:
                Path(tmp_path).unlink(missing_ok=True)

    def _parse_output(
        self,
        result: subprocess.CompletedProcess[str],
    ) -> AnalyzerOutput:
        try:
            data = json.loads(result.stdout)
        except (json.JSONDecodeError, TypeError):
            logger.exception("Failed to parse ESLint JSON output")
            return AnalyzerOutput(
                error="Failed to parse ESLint output",
                raw_output={
                    "stdout": result.stdout,
                    "stderr": result.stderr,
                },
            )

        security_rules = {
            "no-eval",
            "no-implied-eval",
            "no-new-func",
        }
        findings: list[FindingData] = []
        for file_result in data:
            file_path = file_result.get("filePath", "")
            for msg in file_result.get("messages", []):
                raw_severity = msg.get("severity", 1)
                severity = ESLINT_SEVERITY_MAP.get(raw_severity, "medium")

                rule_id = msg.get("ruleId") or ""
                category = "security" if rule_id in security_rules else "quality"

                suggestion = f"See ESLint rule: {rule_id}" if rule_id else ""
                findings.append(
                    FindingData(
                        severity=severity,
                        category=category,
                        title=msg.get("message", "ESLint issue"),
                        description=msg.get("message", ""),
                        suggestion=suggestion,
                        file_path=file_path,
                        line_number=msg.get("line"),
                        column_number=msg.get("column"),
                        code_snippet=msg.get("source", ""),
                        rule_id=rule_id,
                        confidence="high",
                        tool_specific_data={
                            "node_type": msg.get("nodeType", ""),
                            "fatal": msg.get("fatal", False),
                        },
                    ),
                )

        severity_counts = {"critical": 0, "high": 0, "medium": 0, "low": 0, "info": 0}
        for f in findings:
            if f.severity in severity_counts:
                severity_counts[f.severity] += 1

        return AnalyzerOutput(
            findings=findings,
            summary={
                "total_issues": len(findings),
                "by_severity": severity_counts,
            },
            raw_output=data,
        )


class PylintAnalyzer(BaseAnalyzer):
    """Runs Pylint code quality analysis on Python code."""

    name: ClassVar[str] = "pylint"
    analyzer_type: ClassVar[str] = "static"
    display_name: ClassVar[str] = "Pylint Code Quality Analyzer"
    description: ClassVar[str] = (
        "Checks Python code for errors, style, and quality issues."
    )

    def check_available(self) -> tuple[bool, str]:
        try:
            result = subprocess.run(
                ["pylint", "--version"],  # noqa: S607
                capture_output=True,
                text=True,
                timeout=10,
                check=False,
            )
        except FileNotFoundError:
            return False, "Pylint is not installed"
        except subprocess.TimeoutExpired:
            return False, "Pylint version check timed out"
        else:
            if result.returncode == 0:
                version = result.stdout.strip().split("\n")[0]
                return True, f"Pylint {version}"
            return False, "Pylint is not installed"

    def analyze(
        self,
        code: dict[str, str],
        config: dict[str, Any] | None = None,
    ) -> AnalyzerOutput:
        source = _extract_code(code, "backend", PYTHON_EXTENSIONS)
        if not source.strip():
            return AnalyzerOutput(
                summary={"message": "No Python code to analyze"},
            )

        available, _message = self.check_available()
        if not available:
            return AnalyzerOutput(error="Pylint is not installed")

        tmp_path: str | None = None
        try:
            with tempfile.NamedTemporaryFile(
                mode="w",
                suffix=".py",
                delete=False,
            ) as tmp:
                tmp.write(source)
                tmp_path = tmp.name

            result = subprocess.run(  # noqa: S603
                [  # noqa: S607
                    "pylint",
                    "--output-format=json",
                    "--disable=C0114,C0115,C0116",
                    tmp_path,
                ],
                capture_output=True,
                text=True,
                timeout=60,
                check=False,
            )

            return self._parse_output(result)
        except subprocess.TimeoutExpired:
            logger.exception("Pylint analysis timed out")
            return AnalyzerOutput(error="Pylint analysis timed out")
        except Exception:
            logger.exception("Pylint analysis failed")
            return AnalyzerOutput(error="Pylint analysis failed unexpectedly")
        finally:
            if tmp_path:
                Path(tmp_path).unlink(missing_ok=True)

    def _parse_output(
        self,
        result: subprocess.CompletedProcess[str],
    ) -> AnalyzerOutput:
        try:
            data = json.loads(result.stdout)
        except (json.JSONDecodeError, TypeError):
            logger.exception("Failed to parse Pylint JSON output")
            return AnalyzerOutput(
                error="Failed to parse Pylint output",
                raw_output={
                    "stdout": result.stdout,
                    "stderr": result.stderr,
                },
            )

        findings: list[FindingData] = []
        for msg in data:
            msg_type = msg.get("type", "W")[0].upper()
            severity = PYLINT_SEVERITY_MAP.get(msg_type, "medium")
            category = PYLINT_CATEGORY_MAP.get(msg_type, "quality")
            msg_id = msg.get("message-id", "")
            symbol = msg.get("symbol", "")

            findings.append(
                FindingData(
                    severity=severity,
                    category=category,
                    title=msg.get("message", "Pylint issue"),
                    description=msg.get("message", ""),
                    suggestion=f"See Pylint message: {msg_id} ({symbol})",
                    file_path=msg.get("path", ""),
                    line_number=msg.get("line"),
                    column_number=msg.get("column"),
                    code_snippet="",
                    rule_id=msg_id,
                    confidence=("high" if msg_type in ("E", "F") else "medium"),
                    tool_specific_data={
                        "symbol": msg.get("symbol", ""),
                        "module": msg.get("module", ""),
                        "obj": msg.get("obj", ""),
                    },
                ),
            )

        severity_counts = {"critical": 0, "high": 0, "medium": 0, "low": 0, "info": 0}
        category_counts: dict[str, int] = {}
        for f in findings:
            if f.severity in severity_counts:
                severity_counts[f.severity] += 1
            category_counts[f.category] = category_counts.get(f.category, 0) + 1

        return AnalyzerOutput(
            findings=findings,
            summary={
                "total_issues": len(findings),
                "by_severity": severity_counts,
                "by_category": category_counts,
            },
            raw_output=data,
        )

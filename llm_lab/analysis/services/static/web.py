"""Legacy web-oriented static analyzers."""

from __future__ import annotations

import json
import logging
import tempfile
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

_CSS_GLOBS = ("*.css", "*.scss", "*.sass", "*.less")


def _find_css_files(root: Path) -> list[Path]:
    files: list[Path] = []
    for pattern in _CSS_GLOBS:
        files.extend(path for path in root.rglob(pattern) if "node_modules" not in path.parts)
    return sorted(set(files))


def _find_html_files(root: Path) -> list[Path]:
    return sorted(path for path in root.rglob("*.html") if "node_modules" not in path.parts)


def _rel_path(path: str | Path, root: Path) -> str:
    try:
        return str(Path(path).resolve().relative_to(root.resolve()))
    except ValueError:
        return str(path)


class StylelintAnalyzer(BaseAnalyzer):
    name: ClassVar[str] = "stylelint"
    analyzer_type: ClassVar[str] = "static"
    display_name: ClassVar[str] = "Stylelint CSS Linter"
    description: ClassVar[str] = "Modern CSS/SCSS linter for style guide enforcement"
    default_timeout: ClassVar[int] = 60

    def check_available(self) -> tuple[bool, str]:
        return check_cli(["npx", "--version"], tool_name="npx")

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
            css_files = _find_css_files(root)
            if not css_files:
                return AnalyzerOutput(summary={"message": "No CSS files to analyze"})

            stylelint_config = {
                "extends": "stylelint-config-standard",
                "rules": {
                    "at-rule-no-unknown": [True, {"ignoreAtRules": ["tailwind", "apply", "layer", "screen"]}],
                },
            }
            with tempfile.NamedTemporaryFile(mode="w", suffix=".stylelintrc.json", delete=False) as handle:
                json.dump(stylelint_config, handle)
                config_path = Path(handle.name)

            try:
                result = run_subprocess(
                    [
                        "npx",
                        "--yes",
                        "stylelint",
                        "--config",
                        str(config_path),
                        "--formatter",
                        "json",
                        *[str(path) for path in css_files],
                    ],
                    timeout=int(merged.get("timeout", self.default_timeout)),
                    cancel=cancel,
                    cwd=root,
                )
            finally:
                config_path.unlink(missing_ok=True)

            if result is None:
                if cancel and cancel.is_cancelled():
                    return AnalyzerOutput(error="Analysis cancelled")
                return AnalyzerOutput(error="Stylelint analysis timed out")

            payload = result.stdout or result.stderr
            try:
                data = json.loads(payload or "[]")
            except json.JSONDecodeError:
                return AnalyzerOutput(error=f"Stylelint failed: {(result.stderr or result.stdout)[:500]}")

            findings: list[FindingData] = []
            for file_result in data:
                for warning in file_result.get("warnings", []):
                    severity = "high" if warning.get("severity") == "error" else "medium"
                    findings.append(
                        FindingData(
                            severity=severity,
                            category="style",
                            title=warning.get("text", "Stylelint finding"),
                            description=warning.get("text", ""),
                            suggestion="Update the stylesheet to satisfy the Stylelint rule.",
                            file_path=_rel_path(file_result.get("source", ""), root),
                            line_number=int(warning.get("line") or 0) or None,
                            column_number=int(warning.get("column") or 0) or None,
                            rule_id=warning.get("rule", ""),
                            confidence="high",
                        ),
                    )

            return AnalyzerOutput(findings=findings, summary={"total_issues": len(findings)}, raw_output=data)


class HTMLValidatorAnalyzer(BaseAnalyzer):
    name: ClassVar[str] = "html-validator"
    analyzer_type: ClassVar[str] = "static"
    display_name: ClassVar[str] = "HTML Validator"
    description: ClassVar[str] = "Validates HTML files using standard rules"
    default_timeout: ClassVar[int] = 60

    def check_available(self) -> tuple[bool, str]:
        return check_cli(["npx", "--version"], tool_name="npx")

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
        reports: list[dict[str, Any]] = []

        with materialize_analysis_project(code, config=merged) as root:
            html_files = _find_html_files(root)
            if not html_files:
                return AnalyzerOutput(summary={"message": "No HTML files to analyze"})

            for html_file in html_files:
                result = run_subprocess(
                    [
                        "npx",
                        "--yes",
                        "html-validator",
                        f"--file={html_file}",
                        "--format=json",
                        "--verbose",
                    ],
                    timeout=int(merged.get("timeout", self.default_timeout)),
                    cancel=cancel,
                    cwd=root,
                )
                if result is None:
                    if cancel and cancel.is_cancelled():
                        return AnalyzerOutput(error="Analysis cancelled")
                    return AnalyzerOutput(error="HTML validation timed out")

                try:
                    parsed = json.loads(result.stdout or "[]")
                except json.JSONDecodeError:
                    reports.append({"file": str(html_file), "stdout": result.stdout, "stderr": result.stderr})
                    continue

                if isinstance(parsed, dict):
                    parsed = [parsed]
                reports.extend(parsed)
                for item in parsed:
                    for message in item.get("messages", []):
                        severity = (
                            "high" if message.get("type") == "error"
                            else "medium" if message.get("subType") == "warning"
                            else "low"
                        )
                        findings.append(
                            FindingData(
                                severity=severity,
                                category="quality",
                                title=message.get("message", "HTML validation finding"),
                                description=message.get("message", ""),
                                suggestion="Fix the invalid HTML structure or attribute usage.",
                                file_path=_rel_path(item.get("url", html_file), root),
                                line_number=int(message.get("lastLine") or message.get("firstLine") or 0) or None,
                                column_number=(
                                    int(message.get("lastColumn") or message.get("firstColumn") or 0) or None
                                ),
                                rule_id=message.get("messageId", "html-validation"),
                                confidence="high",
                                tool_specific_data={"extract": message.get("extract", "")},
                            ),
                        )

        return AnalyzerOutput(
            findings=findings,
            summary={"total_issues": len(findings), "files_checked": len(reports)},
            raw_output={"reports": reports},
        )

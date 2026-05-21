from __future__ import annotations

import json
import subprocess
from unittest.mock import MagicMock
from unittest.mock import patch

import pytest

from llm_lab.analysis.services.ai_analyzers import CodeQualityAnalyzer
from llm_lab.analysis.services.ai_analyzers import RequirementsScannerAnalyzer
from llm_lab.analysis.services.base import AnalyzerRegistry
from llm_lab.analysis.services.dynamic.legacy import CurlAnalyzer
from llm_lab.analysis.services.dynamic.legacy import CurlEndpointTesterAnalyzer
from llm_lab.analysis.services.performance.load_tests import ArtilleryAnalyzer
from llm_lab.analysis.services.static.legacy import SafetyAnalyzer
from llm_lab.analysis.services.static.legacy import SemgrepAnalyzer
from llm_lab.analysis.services.static.web import StylelintAnalyzer
from llm_lab.generation.tests.factories import AppRequirementTemplateFactory


def _make_popen_mock(stdout: str, *, stderr: str = "", returncode: int = 0) -> MagicMock:
    proc = MagicMock()
    proc.communicate.return_value = (stdout, stderr)
    proc.returncode = returncode
    proc.poll.return_value = returncode
    return proc


def _version_ok(tool: str) -> subprocess.CompletedProcess[str]:
    return subprocess.CompletedProcess([], 0, stdout=f"{tool} 1.0\n", stderr="")


def test_registry_contains_legacy_tool_names():
    names = {item["name"] for item in AnalyzerRegistry.list_available()}
    assert {
        "semgrep",
        "mypy",
        "vulture",
        "ruff",
        "safety",
        "pip-audit",
        "npm-audit",
        "radon",
        "detect-secrets",
        "stylelint",
        "html-validator",
        "curl",
        "nmap",
        "curl-endpoint-tester",
        "locust",
        "ab",
        "aiohttp",
        "artillery",
        "requirements-scanner",
        "code-quality-analyzer",
    }.issubset(names)


class TestSemgrepAnalyzer:
    @patch("llm_lab.analysis.services.base.subprocess.Popen")
    @patch("subprocess.run")
    def test_analyze_returns_findings(self, mock_run, mock_popen):
        mock_run.return_value = _version_ok("semgrep")
        semgrep_output = {
            "results": [
                {
                    "check_id": "python.lang.security.audit.dangerous-system-call",
                    "path": "backend/app.py",
                    "start": {"line": 2, "col": 1},
                    "extra": {
                        "severity": "ERROR",
                        "message": "Dangerous system call",
                        "lines": "os.system(user_input)",
                    },
                },
            ],
        }
        mock_popen.return_value = _make_popen_mock(json.dumps(semgrep_output), returncode=1)

        analyzer = SemgrepAnalyzer()
        output = analyzer.analyze({"backend": "import os\nos.system(user_input)\n"})

        assert output.error is None
        assert len(output.findings) == 1
        assert output.findings[0].severity == "high"
        assert output.findings[0].rule_id == "python.lang.security.audit.dangerous-system-call"


class TestSafetyAnalyzer:
    @patch("llm_lab.analysis.services.base.subprocess.Popen")
    @patch("subprocess.run")
    def test_parses_embedded_json_output(self, mock_run, mock_popen):
        mock_run.return_value = _version_ok("safety")
        payload = {
            "scanned_packages": [{"name": "django"}],
            "vulnerabilities": [
                {
                    "package_name": "django",
                    "analyzed_version": "4.0.0",
                    "advisory": "Example advisory",
                    "fixed_versions": ["4.2.16"],
                    "vulnerability_id": "12345",
                    "CVE": "CVE-2024-0001",
                    "severity": {"cvssv3": {"base_score": 8.2}},
                },
            ],
        }
        stdout = "Warning: deprecated\n" + json.dumps(payload) + "\nMore text"
        mock_popen.return_value = _make_popen_mock(stdout, returncode=1)

        analyzer = SafetyAnalyzer()
        output = analyzer.analyze({"backend": "import django\n"}, config={"generation_job_id": None})

        assert output.error is None
        assert len(output.findings) == 1
        assert output.findings[0].severity == "high"
        assert output.findings[0].rule_id == "CVE-2024-0001"


class TestStylelintAnalyzer:
    @patch("llm_lab.analysis.services.base.subprocess.Popen")
    @patch("subprocess.run")
    def test_analyze_css(self, mock_run, mock_popen):
        mock_run.return_value = _version_ok("npx")
        stylelint_output = [
            {
                "source": "styles.css",
                "warnings": [
                    {
                        "line": 1,
                        "column": 10,
                        "rule": "color-no-invalid-hex",
                        "severity": "error",
                        "text": "Unexpected invalid hex color",
                    },
                ],
            },
        ]
        mock_popen.return_value = _make_popen_mock(json.dumps(stylelint_output), returncode=2)

        analyzer = StylelintAnalyzer()
        output = analyzer.analyze({"styles.css": "body { color: #zzz; }"})

        assert output.error is None
        assert len(output.findings) == 1
        assert output.findings[0].severity == "high"
        assert output.findings[0].rule_id == "color-no-invalid-hex"


class TestCurlAnalyzer:
    @patch("llm_lab.analysis.services.dynamic.legacy._request_url")
    def test_reports_missing_headers_and_slow_response(self, mock_request):
        mock_request.return_value = (
            200,
            {"Server": "test"},
            "<html></html>",
            2500.0,
            None,
        )
        analyzer = CurlAnalyzer()
        output = analyzer.analyze({}, config={"target_url": "https://example.com"})

        assert output.error is None
        rule_ids = {finding.rule_id for finding in output.findings}
        assert "curl/content-security-policy" in rule_ids
        assert "curl/slow-response" in rule_ids


@pytest.mark.django_db
class TestCurlEndpointTesterAnalyzer:
    @patch("llm_lab.analysis.services.dynamic.legacy._request_url")
    def test_uses_app_requirement_endpoints(self, mock_request):
        mock_request.return_value = (404, {}, "missing", 120.0, None)
        template = AppRequirementTemplateFactory(
            api_endpoints=[
                {"path": "/api/items", "method": "GET", "expected_status": 200},
            ],
        )
        analyzer = CurlEndpointTesterAnalyzer()
        output = analyzer.analyze(
            {},
            config={"target_url": "https://example.com", "app_requirement_id": template.id},
        )

        assert output.error is None
        assert output.summary["failed"] == 1
        assert len(output.findings) == 1


class TestPerformanceAnalyzers:
    def test_artillery_load_test_builds_findings(self):
        async def fake_run(*args, **kwargs):
            return {
                "statuses": [200, 200, 500, None],
                "latencies_ms": [100, 150, 2200, 3500],
                "errors": ["boom"],
                "total_requests": 4,
            }

        with (
            patch("llm_lab.analysis.services.performance.load_tests.find_spec", return_value=object()),
            patch("llm_lab.analysis.services.performance.load_tests._run_load_test", side_effect=fake_run),
        ):
            analyzer = ArtilleryAnalyzer()
            output = analyzer.analyze(
                {},
                config={"target_url": "https://example.com", "duration": 2, "arrival_rate": 2},
            )

        assert output.error is None
        assert output.summary["failed_requests"] == 2
        assert any(finding.rule_id == "artillery/failure-rate" for finding in output.findings)


@pytest.mark.django_db
class TestAIAnalyzers:
    @patch("llm_lab.analysis.services.ai_analyzers._get_openrouter_client")
    def test_requirements_scanner_builds_compliance_summary(self, mock_get_client, settings):
        settings.OPENROUTER_API_KEY = "test-key"
        template = AppRequirementTemplateFactory(
            backend_requirements=["Create API endpoint", "Persist records"],
            frontend_requirements=["Render list"],
            admin_requirements=["Provide admin controls"],
        )
        mock_client = MagicMock()
        response = {
            "choices": [
                {
                    "message": {
                        "content": json.dumps(
                            {
                                "backend": [
                                    {
                                        "requirement": "Create API endpoint",
                                        "status": "met",
                                        "confidence": "high",
                                        "explanation": "Route exists.",
                                    },
                                    {
                                        "requirement": "Persist records",
                                        "status": "missing",
                                        "confidence": "high",
                                        "explanation": "No storage logic found.",
                                    },
                                ],
                                "frontend": [
                                    {
                                        "requirement": "Render list",
                                        "status": "partial",
                                        "confidence": "medium",
                                        "explanation": "List renders but lacks empty state.",
                                    },
                                ],
                                "admin": [
                                    {
                                        "requirement": "Provide admin controls",
                                        "status": "missing",
                                        "confidence": "medium",
                                        "explanation": "No admin controls found.",
                                    },
                                ],
                                "summary": {"overall_compliance": 25},
                            },
                        ),
                    },
                },
            ],
        }
        mock_client.chat_completion.return_value = response
        mock_client.extract_content.return_value = response["choices"][0]["message"]["content"]
        mock_get_client.return_value = mock_client

        analyzer = RequirementsScannerAnalyzer()
        output = analyzer.analyze(
            {"backend": "def api(): pass", "frontend": "export default function App() { return null }"},
            config={"app_requirement_id": template.id},
        )

        assert output.error is None
        assert output.summary["total_requirements"] == 4
        assert len(output.findings) == 3

    @patch("llm_lab.analysis.services.ai_analyzers._get_openrouter_client")
    def test_code_quality_analyzer_adds_metric_findings(self, mock_get_client, settings):
        settings.OPENROUTER_API_KEY = "test-key"
        mock_client = MagicMock()
        response = {
            "choices": [
                {
                    "message": {
                        "content": json.dumps(
                            {
                                "metrics": [
                                    {
                                        "metric_id": "error_handling",
                                        "score": 35,
                                        "status": "poor",
                                        "summary": "Errors bubble to users.",
                                        "recommendations": ["Add try/except around external calls"],
                                    },
                                ],
                                "findings": [],
                                "summary": {"overall_score": 52, "strengths": [], "risks": ["Poor resilience"]},
                            },
                        ),
                    },
                },
            ],
        }
        mock_client.chat_completion.return_value = response
        mock_client.extract_content.return_value = response["choices"][0]["message"]["content"]
        mock_get_client.return_value = mock_client

        analyzer = CodeQualityAnalyzer()
        output = analyzer.analyze({"backend": "def run():\n    return do_work()\n"})

        assert output.error is None
        assert output.summary["overall_score"] == 52
        assert any(finding.rule_id == "quality/error_handling" for finding in output.findings)

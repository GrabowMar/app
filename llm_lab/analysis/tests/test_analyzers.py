from __future__ import annotations

import json
import subprocess
from unittest.mock import MagicMock
from unittest.mock import patch

from llm_lab.analysis.services.ai_analyzers import LLMReviewAnalyzer
from llm_lab.analysis.services.base import AnalyzerRegistry
from llm_lab.analysis.services.static_analyzers import BanditAnalyzer
from llm_lab.analysis.services.static_analyzers import ESLintAnalyzer
from llm_lab.analysis.services.static_analyzers import PylintAnalyzer
from llm_lab.generation.services.openrouter_client import OpenRouterError

# Helpers ──────────────────────────────────────────────────────────────────────


def _make_popen_mock(stdout: str, returncode: int = 0) -> MagicMock:
    """Return a mock subprocess.Popen instance for use with run_subprocess."""
    proc = MagicMock()
    proc.communicate.return_value = (stdout, "")
    proc.returncode = returncode
    proc.poll.return_value = returncode
    return proc


def _version_ok(tool: str) -> subprocess.CompletedProcess:
    return subprocess.CompletedProcess([], 0, stdout=f"{tool} 1.0\n", stderr="")


# ── Bandit ────────────────────────────────────────────────────────────────────


class TestBanditAnalyzer:
    def setup_method(self):
        self.analyzer = BanditAnalyzer()
        self.code = {"backend": "import os\nos.system('ls')\n", "frontend": ""}

    @patch("llm_lab.analysis.services.base.subprocess.Popen")
    @patch("subprocess.run")
    def test_analyze_clean_code(self, mock_run, mock_popen):
        mock_run.return_value = _version_ok("bandit")
        mock_popen.return_value = _make_popen_mock(json.dumps({"results": [], "metrics": {}}))

        output = self.analyzer.analyze(self.code)

        assert output.error is None
        assert len(output.findings) == 0
        assert output.summary["total_issues"] == 0

    @patch("llm_lab.analysis.services.base.subprocess.Popen")
    @patch("subprocess.run")
    def test_analyze_with_findings(self, mock_run, mock_popen):
        bandit_results = {
            "results": [
                {
                    "issue_severity": "HIGH",
                    "issue_confidence": "HIGH",
                    "issue_text": "Use of os.system detected",
                    "test_id": "B605",
                    "test_name": "start_process_with_a_shell",
                    "filename": "app.py",
                    "line_number": 2,
                    "col_offset": 0,
                    "code": "os.system('ls')\n",
                    "line_range": [2],
                    "more_info": "https://bandit.readthedocs.io/en/latest/",
                },
            ],
            "metrics": {},
        }
        mock_run.return_value = _version_ok("bandit")
        mock_popen.return_value = _make_popen_mock(json.dumps(bandit_results), returncode=1)

        output = self.analyzer.analyze(self.code)

        assert output.error is None
        assert len(output.findings) == 1
        finding = output.findings[0]
        assert finding.severity == "high"
        assert finding.category == "security"
        assert finding.rule_id == "B605"
        assert finding.confidence == "high"
        assert finding.line_number == 2

    @patch("subprocess.run")
    def test_tool_not_installed(self, mock_run):
        mock_run.side_effect = FileNotFoundError("bandit not found")

        output = self.analyzer.analyze(self.code)

        assert output.error is not None
        assert "not installed" in output.error

    def test_no_python_code(self):
        output = self.analyzer.analyze({"backend": "", "frontend": "alert('hi')"})
        assert output.error is None
        assert len(output.findings) == 0
        assert output.summary.get("message") == "No Python code to analyze"


# ── ESLint ────────────────────────────────────────────────────────────────────


class TestESLintAnalyzer:
    def setup_method(self):
        self.analyzer = ESLintAnalyzer()
        self.code = {"backend": "", "frontend": "var x = 1;\nconsole.log(y);\n"}

    @patch("llm_lab.analysis.services.base.subprocess.Popen")
    @patch("subprocess.run")
    def test_analyze_clean_code(self, mock_run, mock_popen):
        mock_run.return_value = _version_ok("ESLint")
        mock_popen.return_value = _make_popen_mock(
            json.dumps([{"filePath": "file.js", "messages": []}])
        )

        output = self.analyzer.analyze(self.code)

        assert output.error is None
        assert len(output.findings) == 0

    @patch("llm_lab.analysis.services.base.subprocess.Popen")
    @patch("subprocess.run")
    def test_analyze_with_findings(self, mock_run, mock_popen):
        eslint_output = [
            {
                "filePath": "/code/app.js",
                "messages": [
                    {
                        "ruleId": "no-unused-vars",
                        "severity": 1,
                        "message": "'x' is defined but never used",
                        "line": 1,
                        "column": 5,
                        "source": "var x = 1;",
                        "nodeType": "Identifier",
                        "fatal": False,
                    },
                    {
                        "ruleId": "no-undef",
                        "severity": 2,
                        "message": "'y' is not defined",
                        "line": 2,
                        "column": 13,
                        "source": "console.log(y);",
                        "nodeType": "Identifier",
                        "fatal": False,
                    },
                ],
            },
        ]
        mock_run.return_value = _version_ok("ESLint")
        mock_popen.return_value = _make_popen_mock(json.dumps(eslint_output), returncode=1)

        output = self.analyzer.analyze(self.code)

        assert output.error is None
        assert len(output.findings) == 2
        assert output.findings[0].severity == "low"
        assert output.findings[0].rule_id == "no-unused-vars"
        assert output.findings[1].severity == "high"
        assert output.findings[1].rule_id == "no-undef"

    @patch("subprocess.run")
    def test_tool_not_installed(self, mock_run):
        mock_run.side_effect = FileNotFoundError("npx not found")

        output = self.analyzer.analyze(self.code)

        assert output.error is not None
        assert "not installed" in output.error

    def test_no_frontend_code(self):
        output = self.analyzer.analyze({"backend": "print('hi')", "frontend": ""})
        assert output.error is None
        assert len(output.findings) == 0


# ── Pylint ────────────────────────────────────────────────────────────────────


class TestPylintAnalyzer:
    def setup_method(self):
        self.analyzer = PylintAnalyzer()
        self.code = {"backend": "import os\nx = 1\n", "frontend": ""}

    @patch("llm_lab.analysis.services.base.subprocess.Popen")
    @patch("subprocess.run")
    def test_analyze_clean_code(self, mock_run, mock_popen):
        mock_run.return_value = _version_ok("pylint")
        mock_popen.return_value = _make_popen_mock(json.dumps([]))

        output = self.analyzer.analyze(self.code)

        assert output.error is None
        assert len(output.findings) == 0

    @patch("llm_lab.analysis.services.base.subprocess.Popen")
    @patch("subprocess.run")
    def test_analyze_with_findings(self, mock_run, mock_popen):
        pylint_output = [
            {
                "type": "error",
                "module": "app",
                "obj": "",
                "line": 5,
                "column": 0,
                "path": "app.py",
                "symbol": "undefined-variable",
                "message": "Undefined variable 'foo'",
                "message-id": "E0602",
            },
            {
                "type": "warning",
                "module": "app",
                "obj": "",
                "line": 1,
                "column": 0,
                "path": "app.py",
                "symbol": "unused-import",
                "message": "Unused import os",
                "message-id": "W0611",
            },
        ]
        mock_run.return_value = _version_ok("pylint")
        mock_popen.return_value = _make_popen_mock(json.dumps(pylint_output), returncode=4)

        output = self.analyzer.analyze(self.code)

        assert output.error is None
        assert len(output.findings) == 2
        assert output.findings[0].severity == "high"
        assert output.findings[0].rule_id == "E0602"
        assert output.findings[1].severity == "medium"
        assert output.findings[1].rule_id == "W0611"

    @patch("subprocess.run")
    def test_tool_not_installed(self, mock_run):
        mock_run.side_effect = FileNotFoundError("pylint not found")

        output = self.analyzer.analyze(self.code)

        assert output.error is not None
        assert "not installed" in output.error

    def test_no_python_code(self):
        output = self.analyzer.analyze({"backend": "   ", "frontend": ""})
        assert output.error is None
        assert len(output.findings) == 0


# ── LLM Review ────────────────────────────────────────────────────────────────


class TestLLMReviewAnalyzer:
    def _get_analyzer(self):
        return LLMReviewAnalyzer()

    @patch("llm_lab.analysis.services.ai_analyzers.OpenRouterClient")
    def test_analyze_returns_findings(self, mock_client_cls, settings):
        settings.OPENROUTER_API_KEY = "test-key"
        llm_response = {
            "choices": [
                {
                    "message": {
                        "content": json.dumps(
                            {
                                "findings": [
                                    {
                                        "severity": "high",
                                        "category": "security",
                                        "title": "SQL Injection",
                                        "description": "User input not sanitized",
                                        "suggestion": "Use parameterized queries",
                                        "file_path": "app.py",
                                        "line_number": 10,
                                        "code_snippet": "query = f'SELECT ...'",
                                        "rule_id": "AI-SEC-001",
                                        "confidence": "high",
                                    },
                                ],
                                "summary": {
                                    "overall_quality": 6.0,
                                    "security_score": 3.0,
                                },
                            },
                        ),
                    },
                },
            ],
            "usage": {"prompt_tokens": 100, "completion_tokens": 200},
        }

        mock_client = MagicMock()
        mock_client.chat_completion.return_value = llm_response
        mock_client.extract_content.return_value = llm_response["choices"][0]["message"]["content"]
        mock_client.extract_usage.return_value = llm_response["usage"]
        mock_client_cls.return_value = mock_client

        analyzer = self._get_analyzer()
        code = {"backend": "import sqlite3\nquery = 'SELECT * FROM users'"}
        output = analyzer.analyze(code)

        assert output.error is None
        assert len(output.findings) == 1
        assert output.findings[0].severity == "high"
        assert output.findings[0].category == "security"
        assert output.findings[0].title == "SQL Injection"

    def test_api_key_not_configured(self, settings):
        settings.OPENROUTER_API_KEY = ""

        analyzer = self._get_analyzer()
        output = analyzer.analyze({"backend": "print('hello')"})

        assert output.error is not None
        assert "API key" in output.error

    @patch("llm_lab.analysis.services.ai_analyzers.OpenRouterClient")
    def test_api_error_handling(self, mock_client_cls, settings):
        settings.OPENROUTER_API_KEY = "test-key"

        mock_client = MagicMock()
        mock_client.chat_completion.side_effect = OpenRouterError("Rate limited", 429)
        mock_client_cls.return_value = mock_client

        analyzer = self._get_analyzer()
        output = analyzer.analyze({"backend": "print('hello')"})

        assert output.error is not None
        assert "AI review failed" in output.error


# ── Registry ──────────────────────────────────────────────────────────────────


class TestAnalyzerRegistry:
    def test_list_available(self):
        available = AnalyzerRegistry.list_available()
        names = [a["name"] for a in available]
        assert "bandit" in names
        assert "eslint" in names
        assert "pylint" in names
        assert "llm_review" in names

    def test_get_instance_cached(self):
        inst1 = AnalyzerRegistry.get_instance("bandit")
        inst2 = AnalyzerRegistry.get_instance("bandit")
        assert inst1 is not None
        assert inst1 is inst2

    def test_get_nonexistent(self):
        result = AnalyzerRegistry.get_instance("nonexistent_analyzer")
        assert result is None

    def test_analyzer_metadata(self):
        inst = AnalyzerRegistry.get_instance("bandit")
        assert hasattr(inst, "default_timeout")
        assert hasattr(inst, "priority")
        assert isinstance(inst.default_timeout, int)
        assert isinstance(inst.priority, int)

"""AI-powered code analyzers using LLM APIs."""

from __future__ import annotations

import json
import logging
import re
from typing import TYPE_CHECKING
from typing import Any
from typing import ClassVar

if TYPE_CHECKING:
    from llm_lab.analysis.services.cancellation import CancellationToken

from django.conf import settings

from llm_lab.analysis.services.base import AnalyzerOutput
from llm_lab.analysis.services.base import BaseAnalyzer
from llm_lab.analysis.services.base import FindingData
from llm_lab.analysis.services.base import _safe_int
from llm_lab.generation.services.openrouter_client import OpenRouterClient
from llm_lab.generation.services.openrouter_client import OpenRouterError

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """\
You are an expert code reviewer. Analyze the provided code and return findings \
in a specific JSON format.

You MUST return ONLY a valid JSON object (no markdown, no extra text) \
with this structure:

{
  "findings": [
    {
      "severity": "high",
      "category": "security",
      "title": "SQL Injection Vulnerability",
      "description": "Detailed description of the issue",
      "suggestion": "How to fix it",
      "file_path": "app.py",
      "line_number": 42,
      "code_snippet": "the problematic code",
      "rule_id": "AI-SEC-001",
      "confidence": "high"
    }
  ],
  "summary": {
    "overall_quality": 7.5,
    "security_score": 6.0,
    "maintainability_score": 8.0,
    "performance_score": 7.0,
    "key_strengths": ["strength 1", "strength 2"],
    "key_improvements": ["improvement 1", "improvement 2"],
    "compliance_percentage": 75
  }
}

Rules for severity: critical, high, medium, low, info
Rules for category: security, quality, performance, style, best_practice
Rules for confidence: high, medium, low
Rules for rule_id: Use prefixes AI-SEC for security, AI-QUAL for quality, \
AI-PERF for performance, AI-STYLE for style, AI-BP for best_practice, \
followed by a numeric suffix (e.g. AI-SEC-001)."""

CATEGORY_RULE_PREFIX: dict[str, str] = {
    "security": "AI-SEC",
    "quality": "AI-QUAL",
    "performance": "AI-PERF",
    "style": "AI-STYLE",
    "best_practice": "AI-BP",
}

VALID_SEVERITIES = {"critical", "high", "medium", "low", "info"}
VALID_CATEGORIES = {"security", "quality", "performance", "style", "best_practice"}
VALID_CONFIDENCES = {"high", "medium", "low"}
REQUIREMENT_STATUSES = {"met", "partial", "missing"}

QUALITY_METRICS = (
    "error_handling",
    "type_safety",
    "code_organization",
    "documentation",
    "anti_patterns",
    "security_practices",
    "performance_patterns",
    "testing_readiness",
)


def _extract_json(text: str) -> dict[str, Any] | None:
    """Try to extract a JSON object from text that may contain markdown fences."""
    match = re.search(r"```(?:json)?\s*\n?(.*?)\n?\s*```", text, re.DOTALL)
    if match:
        text = match.group(1)

    text = text.strip()
    try:
        data = json.loads(text)
        if isinstance(data, dict):
            return data
    except json.JSONDecodeError:
        pass

    # Last resort: find first { ... last }
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end > start:
        try:
            data = json.loads(text[start : end + 1])
            if isinstance(data, dict):
                return data
        except json.JSONDecodeError:
            pass

    return None


def _normalize_finding(raw: dict[str, Any]) -> FindingData:
    """Map a raw finding dict from the LLM to a FindingData instance."""
    severity = str(raw.get("severity", "info")).lower()
    if severity not in VALID_SEVERITIES:
        severity = "info"

    category = str(raw.get("category", "quality")).lower()
    if category not in VALID_CATEGORIES:
        category = "quality"

    confidence = str(raw.get("confidence", "medium")).lower()
    if confidence not in VALID_CONFIDENCES:
        confidence = "medium"

    rule_id = raw.get("rule_id", "")
    if not rule_id:
        prefix = CATEGORY_RULE_PREFIX.get(category, "AI-QUAL")
        rule_id = f"{prefix}-000"

    return FindingData(
        severity=severity,
        category=category,
        title=raw.get("title", "Untitled Finding"),
        description=raw.get("description", ""),
        suggestion=raw.get("suggestion", ""),
        file_path=raw.get("file_path", ""),
        line_number=_safe_int(raw.get("line_number")) or None,
        column_number=_safe_int(raw.get("column_number")) or None,
        code_snippet=raw.get("code_snippet", ""),
        rule_id=rule_id,
        confidence=confidence,
    )


def _build_user_message(
    code: dict[str, str],
    review_focus: list[str] | None = None,
) -> str:
    """Build the user message containing the code to review."""
    parts: list[str] = []

    if review_focus:
        parts.append(f"Focus areas: {', '.join(review_focus)}\n")

    parts.append("Please review the following code:\n")

    for label, content in code.items():
        parts.append(f"--- {label} ---")
        parts.append(content)
        parts.append("")

    return "\n".join(parts)


def _get_openrouter_client() -> OpenRouterClient:
    from llm_lab.credentials.services.resolver import MissingApiKeyError
    from llm_lab.credentials.services.resolver import get_openrouter_key

    try:
        api_key = get_openrouter_key(user=None)
    except MissingApiKeyError as exc:
        msg = f"AI analysis unavailable: {exc}"
        raise OpenRouterError(msg) from exc
    return OpenRouterClient(api_key=api_key)


def _truncate_code_for_ai(code: dict[str, str], limit: int) -> str:
    parts: list[str] = []
    for label, content in code.items():
        if not content or not content.strip():
            continue
        parts.append(f"--- {label} ---\n{content.strip()}")
    joined = "\n\n".join(parts)
    return joined[:limit]


def _get_app_requirement(config: dict[str, Any]) -> Any | None:
    app_requirement_id = config.get("app_requirement_id")
    generation_job_id = config.get("generation_job_id")

    from llm_lab.generation.models import AppRequirementTemplate
    from llm_lab.generation.models import GenerationJob

    if app_requirement_id:
        return AppRequirementTemplate.objects.filter(id=app_requirement_id).first()
    if generation_job_id:
        job = GenerationJob.objects.select_related("app_requirement").filter(id=generation_job_id).first()
        return getattr(job, "app_requirement", None)
    return None


class LLMReviewAnalyzer(BaseAnalyzer):
    """AI-powered comprehensive code review using large language models."""

    name: ClassVar[str] = "llm_review"
    analyzer_type: ClassVar[str] = "ai"
    display_name: ClassVar[str] = "AI Code Review"
    description: ClassVar[str] = "AI-powered comprehensive code review using large language models"
    default_config: ClassVar[dict[str, Any]] = {
        "model": "openai/gpt-4o-mini",
        "temperature": 0.2,
        "max_tokens": 8000,
    }

    def check_available(self) -> tuple[bool, str]:
        api_key = getattr(settings, "OPENROUTER_API_KEY", None)
        if not api_key:
            return False, "OpenRouter API key not configured"
        return True, "Available"

    def analyze(
        self,
        code: dict[str, str],
        config: dict[str, Any] | None = None,
        *,
        cancel: CancellationToken | None = None,
    ) -> AnalyzerOutput:
        # Check for cancellation before making a potentially long API call.
        if cancel is not None and cancel.is_cancelled():
            return AnalyzerOutput(error="Analysis cancelled")

        available, message = self.get_availability()
        if not available:
            return AnalyzerOutput(error=message)

        merged = {**self.default_config, **(config or {})}
        model: str = merged["model"]
        temperature: float = merged["temperature"]
        max_tokens: int = merged["max_tokens"]
        review_focus: list[str] | None = merged.get("review_focus")

        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": _build_user_message(code, review_focus)},
        ]

        try:
            from llm_lab.credentials.services.resolver import MissingApiKeyError
            from llm_lab.credentials.services.resolver import get_openrouter_key

            try:
                api_key = get_openrouter_key(user=None)
            except MissingApiKeyError as exc:
                return AnalyzerOutput(error=f"AI review unavailable: {exc}")

            client = OpenRouterClient(api_key=api_key)
            response = client.chat_completion(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )
        except OpenRouterError as exc:
            logger.exception("AI review API call failed")
            return AnalyzerOutput(error=f"AI review failed: {exc}")
        except Exception as exc:
            logger.exception("Unexpected error during AI review")
            return AnalyzerOutput(error=f"AI review failed: {exc}")

        content = client.extract_content(response)
        usage = client.extract_usage(response)

        return self._parse_response(content, usage, response)

    def _parse_response(
        self,
        content: str,
        usage: dict[str, Any],
        raw_response: dict[str, Any],
    ) -> AnalyzerOutput:
        parsed = _extract_json(content)

        if parsed is not None:
            return self._build_output_from_json(parsed, usage, raw_response)

        finding = FindingData(
            severity="info",
            category="quality",
            title="AI Code Review",
            description=content,
            suggestion="",
            rule_id="AI-QUAL-000",
            confidence="low",
        )
        return AnalyzerOutput(
            findings=[finding],
            summary={
                "token_usage": usage,
                "parse_error": "Could not parse structured JSON from LLM response",
            },
            raw_output={"response": raw_response, "content": content},
        )

    def _build_output_from_json(
        self,
        parsed: dict[str, Any],
        usage: dict[str, Any],
        raw_response: dict[str, Any],
    ) -> AnalyzerOutput:
        findings = [_normalize_finding(f) for f in parsed.get("findings", []) if isinstance(f, dict)]

        llm_summary: dict[str, Any] = parsed.get("summary", {})
        summary = {
            **llm_summary,
            "token_usage": usage,
            "total_findings": len(findings),
        }

        return AnalyzerOutput(
            findings=findings,
            summary=summary,
            raw_output={"response": raw_response, "parsed": parsed},
        )


class RequirementsScannerAnalyzer(BaseAnalyzer):
    """AI-powered requirements compliance analysis against the selected template."""

    name: ClassVar[str] = "requirements-scanner"
    analyzer_type: ClassVar[str] = "ai"
    display_name: ClassVar[str] = "Requirements Scanner"
    description: ClassVar[str] = "Checks generated code against backend, frontend, and admin requirements"
    default_config: ClassVar[dict[str, Any]] = {
        "model": "openai/gpt-4o-mini",
        "temperature": 0.1,
        "max_tokens": 4000,
        "scan_mode": "full",
        "max_code_chars": 30000,
    }

    def check_available(self) -> tuple[bool, str]:
        api_key = getattr(settings, "OPENROUTER_API_KEY", None)
        if not api_key:
            return False, "OpenRouter API key not configured"
        return True, "Available"

    def analyze(
        self,
        code: dict[str, str],
        config: dict[str, Any] | None = None,
        *,
        cancel: CancellationToken | None = None,
    ) -> AnalyzerOutput:
        if cancel is not None and cancel.is_cancelled():
            return AnalyzerOutput(error="Analysis cancelled")

        merged = {**self.default_config, **(config or {})}
        app_requirement = _get_app_requirement(merged)
        if app_requirement is None:
            return AnalyzerOutput(
                error="Requirements scanner needs an analysis template from the linked generation job",
            )

        requirement_groups = self._select_requirement_groups(app_requirement, str(merged["scan_mode"]))
        if not any(requirement_groups.values()):
            return AnalyzerOutput(summary={"message": "No requirements defined for this template"})

        prompt = json.dumps(
            {
                "template": {
                    "name": app_requirement.name,
                    "slug": app_requirement.slug,
                    "backend_requirements": requirement_groups["backend"],
                    "frontend_requirements": requirement_groups["frontend"],
                    "admin_requirements": requirement_groups["admin"],
                },
                "code": _truncate_code_for_ai(code, int(merged["max_code_chars"])),
            },
            indent=2,
        )
        messages = [
            {
                "role": "system",
                "content": (
                    "You evaluate whether generated code satisfies explicit application requirements. "
                    "Return ONLY valid JSON with this shape: "
                    '{"backend":[{"requirement":"...","status":"met|partial|missing","confidence":"high|medium|low","explanation":"..."}],'
                    '"frontend":[...],"admin":[...],"summary":{"overall_compliance":0,"notes":[]}}. '
                    "Mark a requirement as met only when the code clearly implements it."
                ),
            },
            {"role": "user", "content": prompt},
        ]

        try:
            client = _get_openrouter_client()
            response = client.chat_completion(
                model=str(merged["model"]),
                messages=messages,
                temperature=float(merged["temperature"]),
                max_tokens=int(merged["max_tokens"]),
            )
        except OpenRouterError as exc:
            logger.exception("Requirements scan failed")
            return AnalyzerOutput(error=f"Requirements scan failed: {exc}")

        parsed = _extract_json(client.extract_content(response))
        if parsed is None:
            return AnalyzerOutput(
                error="Requirements scan returned invalid JSON",
                raw_output={"response": response},
            )

        findings: list[FindingData] = []
        totals: dict[str, dict[str, int]] = {}
        for section in ("backend", "frontend", "admin"):
            entries = parsed.get(section, [])
            status_counts = {"met": 0, "partial": 0, "missing": 0}
            if not isinstance(entries, list):
                entries = []
            for entry in entries:
                if not isinstance(entry, dict):
                    continue
                status = str(entry.get("status", "missing")).lower()
                if status not in REQUIREMENT_STATUSES:
                    status = "missing"
                status_counts[status] += 1
                if status == "met":
                    continue
                severity = "low" if status == "partial" else "medium"
                findings.append(
                    FindingData(
                        severity=severity,
                        category="best_practice",
                        title=f"{section.capitalize()} requirement not fully satisfied",
                        description=str(entry.get("requirement", "")),
                        suggestion=str(entry.get("explanation", "")),
                        rule_id=f"requirements/{section}/{status}",
                        confidence=str(entry.get("confidence", "medium")).lower(),
                        tool_specific_data={"section": section, "status": status},
                    ),
                )
            totals[section] = status_counts

        total_requirements = sum(sum(section.values()) for section in totals.values())
        total_met = sum(section["met"] for section in totals.values())
        overall_compliance = round((total_met / total_requirements) * 100, 2) if total_requirements else 0.0

        return AnalyzerOutput(
            findings=findings,
            summary={
                "overall_compliance": overall_compliance,
                "requirements": totals,
                "total_requirements": total_requirements,
            },
            raw_output={"response": response, "parsed": parsed},
        )

    @staticmethod
    def _select_requirement_groups(app_requirement: Any, scan_mode: str) -> dict[str, list[str]]:
        groups = {
            "backend": list(app_requirement.backend_requirements or []),
            "frontend": list(app_requirement.frontend_requirements or []),
            "admin": list(app_requirement.admin_requirements or []),
        }
        if scan_mode == "backend_only":
            groups["frontend"] = []
            groups["admin"] = []
        elif scan_mode == "frontend_only":
            groups["backend"] = []
            groups["admin"] = []
        elif scan_mode == "admin_only":
            groups["backend"] = []
            groups["frontend"] = []
        return groups


class CodeQualityAnalyzer(BaseAnalyzer):
    """AI-powered code quality scoring based on the legacy analysis dimensions."""

    name: ClassVar[str] = "code-quality-analyzer"
    analyzer_type: ClassVar[str] = "ai"
    display_name: ClassVar[str] = "Code Quality Analyzer"
    description: ClassVar[str] = (
        "Scores generated code across error handling, structure, security, and maintainability"
    )
    default_config: ClassVar[dict[str, Any]] = {
        "model": "openai/gpt-4o-mini",
        "temperature": 0.1,
        "max_tokens": 3500,
        "max_code_chars": 30000,
    }

    def check_available(self) -> tuple[bool, str]:
        api_key = getattr(settings, "OPENROUTER_API_KEY", None)
        if not api_key:
            return False, "OpenRouter API key not configured"
        return True, "Available"

    def analyze(
        self,
        code: dict[str, str],
        config: dict[str, Any] | None = None,
        *,
        cancel: CancellationToken | None = None,
    ) -> AnalyzerOutput:
        if cancel is not None and cancel.is_cancelled():
            return AnalyzerOutput(error="Analysis cancelled")

        merged = {**self.default_config, **(config or {})}
        messages = [
            {
                "role": "system",
                "content": (
                    "You are a strict software quality assessor. "
                    "Return ONLY valid JSON with this shape: "
                    '{"metrics":[{"metric_id":"error_handling","score":0,"status":"good|needs_work|poor","summary":"...",'
                    '"recommendations":["..."]}],"findings":[{"severity":"high","category":"quality","title":"...",'
                    '"description":"...","suggestion":"...","rule_id":"AI-QUAL-001","confidence":"high"}],'
                    '"summary":{"overall_score":0,"strengths":[],"risks":[]}}. '
                    "Scores are 0-100 and metric_id must be one of: "
                    + ", ".join(QUALITY_METRICS)
                    + "."
                ),
            },
            {
                "role": "user",
                "content": _truncate_code_for_ai(code, int(merged["max_code_chars"])),
            },
        ]

        try:
            client = _get_openrouter_client()
            response = client.chat_completion(
                model=str(merged["model"]),
                messages=messages,
                temperature=float(merged["temperature"]),
                max_tokens=int(merged["max_tokens"]),
            )
        except OpenRouterError as exc:
            logger.exception("Code quality analysis failed")
            return AnalyzerOutput(error=f"Code quality analysis failed: {exc}")

        parsed = _extract_json(client.extract_content(response))
        if parsed is None:
            return AnalyzerOutput(
                error="Code quality analysis returned invalid JSON",
                raw_output={"response": response},
            )

        findings = [_normalize_finding(item) for item in parsed.get("findings", []) if isinstance(item, dict)]
        metric_scores: dict[str, Any] = {}
        for metric in parsed.get("metrics", []):
            if not isinstance(metric, dict):
                continue
            metric_id = str(metric.get("metric_id", ""))
            if metric_id not in QUALITY_METRICS:
                continue
            metric_scores[metric_id] = {
                "score": _safe_int(metric.get("score")),
                "status": metric.get("status", "needs_work"),
                "summary": metric.get("summary", ""),
                "recommendations": metric.get("recommendations", []),
            }
            score = _safe_int(metric.get("score"))
            if score >= 70:
                continue
            severity = "high" if score < 40 else "medium"
            findings.append(
                FindingData(
                    severity=severity,
                    category="quality",
                    title=f"Weak {metric_id.replace('_', ' ')}",
                    description=str(metric.get("summary", "")),
                    suggestion="; ".join(str(item) for item in metric.get("recommendations", [])[:3]),
                    rule_id=f"quality/{metric_id}",
                    confidence="medium",
                ),
            )

        overall_score = _safe_int((parsed.get("summary") or {}).get("overall_score"))
        return AnalyzerOutput(
            findings=findings,
            summary={
                "overall_score": overall_score,
                "metrics": metric_scores,
                "strengths": (parsed.get("summary") or {}).get("strengths", []),
                "risks": (parsed.get("summary") or {}).get("risks", []),
            },
            raw_output={"response": response, "parsed": parsed},
        )

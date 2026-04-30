"""Export services — CSV, JSON, SARIF for findings, jobs, tasks, and reports."""

from __future__ import annotations

import csv
import io
from typing import TYPE_CHECKING
from typing import Any

if TYPE_CHECKING:
    from django.db.models import QuerySet


# ── Severity → SARIF level mapping ──────────────────────────────────────────

_SARIF_LEVEL: dict[str, str] = {
    "critical": "error",
    "high": "error",
    "medium": "warning",
    "low": "note",
    "info": "note",
}

# ── Findings ─────────────────────────────────────────────────────────────────

FINDING_HEADERS = [
    "id",
    "task_id",
    "analyzer",
    "severity",
    "file_path",
    "line",
    "rule_id",
    "message",
    "cwe",
    "created_at",
]


def findings_csv(queryset: QuerySet[Any]) -> str:
    """Return CSV string of findings."""
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(FINDING_HEADERS)
    for f in queryset.select_related("result", "result__task"):
        writer.writerow(
            [
                str(f.id),
                str(f.result.task_id),
                f.result.analyzer_name,
                f.severity,
                f.file_path,
                f.line_number or "",
                f.rule_id,
                f.title,
                f.tool_specific_data.get("cwe", "") if f.tool_specific_data else "",
                f.created_at.isoformat(),
            ],
        )
    return buf.getvalue()


def findings_json(queryset: QuerySet[Any]) -> list[dict[str, Any]]:
    """Return list of finding dicts."""
    return [
        {
            "id": f.id,
            "task_id": str(f.result.task_id),
            "analyzer": f.result.analyzer_name,
            "severity": f.severity,
            "file_path": f.file_path,
            "line": f.line_number,
            "rule_id": f.rule_id,
            "message": f.title,
            "cwe": f.tool_specific_data.get("cwe", "") if f.tool_specific_data else "",
            "created_at": f.created_at.isoformat(),
        }
        for f in queryset.select_related("result", "result__task")
    ]


def findings_sarif(queryset: QuerySet[Any]) -> dict[str, Any]:
    """Return SARIF 2.1.0 dict grouped by analyzer name."""
    # Group findings by analyzer
    by_analyzer: dict[str, list[Any]] = {}
    for f in queryset.select_related("result", "result__task"):
        key = f.result.analyzer_name
        by_analyzer.setdefault(key, []).append(f)

    runs = []
    for analyzer_name, findings in by_analyzer.items():
        results_list = []
        for f in findings:
            result_entry: dict[str, Any] = {
                "ruleId": f.rule_id or "unknown",
                "level": _SARIF_LEVEL.get(f.severity, "warning"),
                "message": {"text": f.title},
                "locations": [],
            }
            if f.file_path:
                location: dict[str, Any] = {
                    "physicalLocation": {
                        "artifactLocation": {"uri": f.file_path},
                    },
                }
                if f.line_number:
                    location["physicalLocation"]["region"] = {
                        "startLine": f.line_number,
                    }
                result_entry["locations"].append(location)
            results_list.append(result_entry)

        runs.append(
            {
                "tool": {
                    "driver": {
                        "name": analyzer_name,
                        "version": "1.0.0",
                        "informationUri": "",
                    },
                },
                "results": results_list,
            },
        )

    return {
        "version": "2.1.0",
        "$schema": "https://raw.githubusercontent.com/oasis-tcs/sarif-spec/master/Schemata/sarif-schema-2.1.0.json",
        "runs": runs,
    }


# ── Generation jobs ───────────────────────────────────────────────────────────

_JOB_HEADERS = [
    "id",
    "model",
    "template",
    "status",
    "started_at",
    "completed_at",
    "tokens_used",
    "duration",
]


def _job_tokens(job: Any) -> int | str:
    metrics = job.metrics or {}
    return metrics.get("total_tokens", metrics.get("tokens_used", ""))


def _job_template(job: Any) -> str:
    if job.scaffolding_template_id:
        try:
            return job.scaffolding_template.name
        except AttributeError:
            return str(job.scaffolding_template_id)
    if job.app_requirement_id:
        try:
            return job.app_requirement.name
        except AttributeError:
            return str(job.app_requirement_id)
    return ""


def generation_jobs_csv(queryset: QuerySet[Any]) -> str:
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(_JOB_HEADERS)
    for job in queryset.select_related(
        "model",
        "scaffolding_template",
        "app_requirement",
    ):
        writer.writerow(
            [
                str(job.id),
                job.model.name if job.model_id else "",
                _job_template(job),
                job.status,
                job.started_at.isoformat() if job.started_at else "",
                job.completed_at.isoformat() if job.completed_at else "",
                _job_tokens(job),
                job.duration_seconds if job.duration_seconds is not None else "",
            ],
        )
    return buf.getvalue()


def generation_jobs_json(queryset: QuerySet[Any]) -> list[dict[str, Any]]:
    return [
        {
            "id": str(job.id),
            "model": job.model.name if job.model_id else None,
            "template": _job_template(job) or None,
            "status": job.status,
            "started_at": job.started_at.isoformat() if job.started_at else None,
            "completed_at": job.completed_at.isoformat() if job.completed_at else None,
            "tokens_used": _job_tokens(job) or None,
            "duration": job.duration_seconds,
        }
        for job in queryset.select_related(
            "model",
            "scaffolding_template",
            "app_requirement",
        )
    ]


# ── Analysis tasks ────────────────────────────────────────────────────────────

_TASK_HEADERS = [
    "id",
    "name",
    "status",
    "target",
    "critical",
    "high",
    "medium",
    "low",
    "info",
    "duration",
    "created",
]


def _task_severity_counts(task: Any) -> dict[str, int]:
    summary = task.results_summary or {}
    # Try flattened keys first, then nested
    if "critical" in summary or "high" in summary:
        return {
            "critical": summary.get("critical", 0),
            "high": summary.get("high", 0),
            "medium": summary.get("medium", 0),
            "low": summary.get("low", 0),
            "info": summary.get("info", 0),
        }
    counts = summary.get("severity_counts", {})
    return {
        "critical": counts.get("critical", 0),
        "high": counts.get("high", 0),
        "medium": counts.get("medium", 0),
        "low": counts.get("low", 0),
        "info": counts.get("info", 0),
    }


def _task_target(task: Any) -> str:
    if task.generation_job_id:
        return f"job:{task.generation_job_id}"
    if task.source_code:
        keys = list((task.source_code or {}).keys())
        return "inline:" + ",".join(keys)
    return ""


def analysis_tasks_csv(queryset: QuerySet[Any]) -> str:
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(_TASK_HEADERS)
    for task in queryset:
        counts = _task_severity_counts(task)
        writer.writerow(
            [
                str(task.id),
                task.name,
                task.status,
                _task_target(task),
                counts["critical"],
                counts["high"],
                counts["medium"],
                counts["low"],
                counts["info"],
                task.duration_seconds if task.duration_seconds is not None else "",
                task.created_at.isoformat(),
            ],
        )
    return buf.getvalue()


def analysis_tasks_json(queryset: QuerySet[Any]) -> list[dict[str, Any]]:
    return [
        {
            "id": str(task.id),
            "name": task.name,
            "status": task.status,
            "target": _task_target(task),
            "severity_counts": _task_severity_counts(task),
            "duration": task.duration_seconds,
            "created": task.created_at.isoformat(),
        }
        for task in queryset
    ]


# ── Reports ───────────────────────────────────────────────────────────────────

_REPORT_HEADERS = ["id", "title", "type", "status", "created"]


def reports_csv(queryset: QuerySet[Any]) -> str:
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(_REPORT_HEADERS)
    for report in queryset:
        writer.writerow(
            [
                str(report.id),
                report.title,
                report.report_type,
                report.status,
                report.created_at.isoformat(),
            ],
        )
    return buf.getvalue()


def reports_json(queryset: QuerySet[Any]) -> list[dict[str, Any]]:
    return [
        {
            "id": str(report.id),
            "title": report.title,
            "type": report.report_type,
            "status": report.status,
            "created": report.created_at.isoformat(),
        }
        for report in queryset
    ]

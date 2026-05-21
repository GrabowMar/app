"""Handles result persistence, finding storage, and aggregation."""

from __future__ import annotations

import logging
from collections import Counter
from typing import Any

from django.db import transaction
from django.db.models import Count
from django.db.models import Q
from django.utils import timezone

from llm_lab.analysis.models import AnalysisResult
from llm_lab.analysis.models import AnalysisTask
from llm_lab.analysis.models import Finding
from llm_lab.analysis.services.base import AnalyzerOutput
from llm_lab.analysis.services.base import AnalyzerRegistry
from llm_lab.analysis.services.base import BaseAnalyzer
from llm_lab.analysis.services.base import FindingData
from llm_lab.realtime import events as realtime

logger = logging.getLogger(__name__)


def _compute_duration(started_at: Any, completed_at: Any) -> float:
    return (completed_at - started_at).total_seconds()


_RESULT_SAVE_FIELDS = [
    "status",
    "error_message",
    "completed_at",
    "duration_seconds",
]


class ResultService:
    """Handles result persistence, finding storage, and aggregation."""

    def create_results(
        self,
        task: AnalysisTask,
        analyzer_names: list[str],
        settings: dict[str, Any],
    ) -> list[tuple[AnalysisResult, BaseAnalyzer, dict[str, Any] | None]]:
        """Create AnalysisResult records for each analyzer.

        Uses a single bulk INSERT for all result rows, then a single bulk UPDATE
        for any that must be marked SKIPPED (unknown analyzer name).

        Returns a list of ``(result, analyzer, config)`` tuples for runnable
        analyzers.
        """
        # Resolve analyzers up-front so we touch the registry once per name.
        resolved: list[tuple[str, BaseAnalyzer | None]] = [
            (name, AnalyzerRegistry.get_instance(name)) for name in analyzer_names
        ]

        # One bulk INSERT instead of N individual creates.
        result_objects = AnalysisResult.objects.bulk_create(
            [
                AnalysisResult(
                    task=task,
                    analyzer_name=name,
                    analyzer_type=(analyzer.analyzer_type if analyzer else ""),
                    status=AnalysisResult.Status.PENDING,
                )
                for name, analyzer in resolved
            ]
        )

        runnable: list[tuple[AnalysisResult, BaseAnalyzer, dict[str, Any] | None]] = []
        skipped: list[AnalysisResult] = []

        for result_obj, (name, analyzer) in zip(result_objects, resolved):
            if analyzer is None:
                logger.warning("Analyzer %r not found, skipping", name)
                result_obj.status = AnalysisResult.Status.SKIPPED
                result_obj.error_message = f"Analyzer '{name}' is not registered."
                skipped.append(result_obj)
            else:
                runnable.append((result_obj, analyzer, settings.get(name)))

        if skipped:
            # One bulk UPDATE instead of M individual saves.
            AnalysisResult.objects.bulk_update(skipped, ["status", "error_message"])

        return runnable

    def save_findings(self, result: AnalysisResult, findings: list[FindingData]) -> int:
        """Bulk-create Finding records. Returns count created.

        Callers that need findings and a result status update to be atomic
        should call this inside their own ``transaction.atomic()`` block.
        """
        if not findings:
            return 0
        Finding.objects.bulk_create(
            [
                Finding(
                    result=result,
                    severity=f.severity,
                    category=f.category,
                    confidence=f.confidence,
                    title=f.title,
                    description=f.description,
                    suggestion=f.suggestion,
                    file_path=f.file_path,
                    line_number=f.line_number,
                    column_number=f.column_number,
                    code_snippet=f.code_snippet,
                    rule_id=f.rule_id,
                    tool_specific_data=f.tool_specific_data,
                )
                for f in findings
            ]
        )
        return len(findings)

    def save_analyzer_output(
        self,
        result: AnalysisResult,
        output: AnalyzerOutput,
        analyzer: BaseAnalyzer,
    ) -> None:
        """Persist a single analyzer's output and broadcast a live update.

        The finding INSERT and result UPDATE are wrapped in a single atomic
        block so that partial writes (findings committed, result still PENDING)
        cannot occur.  ``realtime.publish`` fires after the transaction commits.
        """
        finding_count = 0
        severity_counts: dict[str, int] = {}

        with transaction.atomic():
            if output.has_error:
                result.status = AnalysisResult.Status.FAILED
                result.error_message = output.error or ""
            else:
                result.status = AnalysisResult.Status.COMPLETED
                finding_count = self.save_findings(result, output.findings)
                severity_counts = dict(Counter(f.severity for f in output.findings))

            result.raw_output = output.raw_output
            result.summary = output.summary
            result.completed_at = timezone.now()
            result.duration_seconds = _compute_duration(result.started_at, result.completed_at)
            result.save(update_fields=[*_RESULT_SAVE_FIELDS, "raw_output", "summary"])

        if finding_count:
            logger.info("Analyzer %s produced %d findings", analyzer.name, finding_count)

        # SSE fires after the transaction commits — listeners that poll the REST
        # API on receiving this event see consistent data.
        realtime.publish(
            f"analysis:{result.task_id}",
            {
                "type": "result",
                "analyzer": result.analyzer_name,
                "status": result.status,
                "finding_count": finding_count,
                "severity_counts": severity_counts,
                "updated_at": result.completed_at.isoformat() if result.completed_at else None,
            },
        )

    def mark_result_failed(self, result: AnalysisResult, error_msg: str) -> None:
        result.status = AnalysisResult.Status.FAILED
        result.error_message = error_msg
        result.completed_at = timezone.now()
        if result.started_at:
            result.duration_seconds = _compute_duration(result.started_at, result.completed_at)
        result.save(update_fields=_RESULT_SAVE_FIELDS)

    def mark_result_cancelled(self, result: AnalysisResult) -> None:
        result.status = AnalysisResult.Status.CANCELLED
        result.error_message = "Analysis cancelled by user"
        result.completed_at = timezone.now()
        if result.started_at:
            result.duration_seconds = _compute_duration(result.started_at, result.completed_at)
        result.save(update_fields=_RESULT_SAVE_FIELDS)

    def aggregate_results(self, task: AnalysisTask) -> dict[str, Any]:
        """Compute aggregate summary from all results.

        All counts are computed in the database — no Python-side table scans.

        Query plan:
          1. Annotated result queryset  (1 query, O(analyzers))
          2. GROUP BY severity          (1 query, at most 5 rows)
          3. GROUP BY category          (1 query, at most 7 rows)
        """
        results = list(
            task.results.annotate(finding_count=Count("findings")).order_by("analyzer_name")
        )
        base_qs = Finding.objects.filter(result__task=task)

        # DB-level GROUP BY — never loads individual finding rows into Python.
        severity_map: dict[str, int] = {
            row["severity"]: row["count"]
            for row in base_qs.values("severity").annotate(count=Count("id"))
        }
        category_map: dict[str, int] = {
            row["category"]: row["count"]
            for row in base_qs.values("category").annotate(count=Count("id"))
        }

        by_severity: dict[str, int] = {s.value: severity_map.get(s.value, 0) for s in Finding.Severity}
        by_category: dict[str, int] = {c.value: category_map.get(c.value, 0) for c in Finding.Category}

        completed = 0
        failed = 0
        by_analyzer: dict[str, dict[str, Any]] = {}
        for r in results:
            by_analyzer[r.analyzer_name] = {
                "status": r.status,
                "findings": r.finding_count,  # from annotation — no extra query
                "duration": r.duration_seconds,
            }
            if r.status == AnalysisResult.Status.COMPLETED:
                completed += 1
            elif r.status == AnalysisResult.Status.FAILED:
                failed += 1

        total_findings = sum(severity_map.values())

        return {
            "total_findings": total_findings,
            "by_severity": by_severity,
            "by_category": by_category,
            "by_analyzer": by_analyzer,
            "analyzers_completed": completed,
            "analyzers_failed": failed,
            "analyzers_total": len(results),
        }

    def finalize_task(self, task: AnalysisTask) -> None:
        """Set final task status and persist the aggregated summary.

        If the task was cancelled externally this method is a no-op so the
        CANCELLED status set by the API endpoint is not overwritten.
        """
        # Re-read status to detect an external cancellation.
        task.refresh_from_db(fields=["status"])
        if task.status == AnalysisTask.Status.CANCELLED:
            logger.info("Task %s was cancelled; skipping finalization", task.id)
            return

        task.results_summary = self.aggregate_results(task)

        # Single aggregate query replaces three separate count queries.
        counts = task.results.aggregate(
            total=Count("id"),
            completed=Count("id", filter=Q(status=AnalysisResult.Status.COMPLETED)),
            failed=Count("id", filter=Q(status=AnalysisResult.Status.FAILED)),
        )
        completed_count = counts["completed"] or 0
        failed_count = counts["failed"] or 0
        total = counts["total"] or 0

        if completed_count == total:
            task.status = AnalysisTask.Status.COMPLETED
        elif failed_count == total:
            task.status = AnalysisTask.Status.FAILED
        else:
            task.status = AnalysisTask.Status.PARTIAL

        task.completed_at = timezone.now()
        if task.started_at:
            task.duration_seconds = _compute_duration(task.started_at, task.completed_at)
        task.save(
            update_fields=[
                "status",
                "results_summary",
                "completed_at",
                "duration_seconds",
            ],
        )
        logger.info(
            "Analysis task %s finished: %s (%d/%d completed)",
            task.id,
            task.status,
            completed_count,
            total,
        )
        realtime.publish(
            f"analysis:{task.id}",
            {
                "type": "status",
                "status": task.status,
                "updated_at": task.completed_at.isoformat() if task.completed_at else None,
            },
        )

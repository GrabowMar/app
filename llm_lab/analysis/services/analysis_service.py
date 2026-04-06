"""Orchestrator that runs analysis tasks across multiple analyzers."""

from __future__ import annotations

import importlib
import logging
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import as_completed
from typing import Any

from django.db import transaction
from django.utils import timezone

from llm_lab.analysis.models import AnalysisResult
from llm_lab.analysis.models import AnalysisTask
from llm_lab.analysis.models import Finding
from llm_lab.analysis.services.base import AnalyzerOutput
from llm_lab.analysis.services.base import AnalyzerRegistry
from llm_lab.analysis.services.base import BaseAnalyzer
from llm_lab.analysis.services.base import FindingData

logger = logging.getLogger(__name__)

_ANALYZER_MODULES = [
    "llm_lab.analysis.services.static_analyzers",
    "llm_lab.analysis.services.dynamic_analyzers",
    "llm_lab.analysis.services.performance_analyzers",
    "llm_lab.analysis.services.ai_analyzers",
]


def _ensure_analyzers_registered() -> None:
    """Import analyzer modules so subclasses register via __init_subclass__."""
    for mod in _ANALYZER_MODULES:
        try:
            importlib.import_module(mod)
        except ModuleNotFoundError:
            logger.debug("Analyzer module %s not found, skipping", mod)


def _set_task_failed(
    task: AnalysisTask,
    message: str,
) -> None:
    task.status = AnalysisTask.Status.FAILED
    task.error_message = message
    task.completed_at = timezone.now()
    if task.started_at:
        delta = task.completed_at - task.started_at
        task.duration_seconds = delta.total_seconds()
    task.save(
        update_fields=[
            "status",
            "error_message",
            "completed_at",
            "duration_seconds",
        ],
    )


def _compute_duration(
    started_at: Any,
    completed_at: Any,
) -> float:
    return (completed_at - started_at).total_seconds()


_RESULT_SAVE_FIELDS = [
    "status",
    "error_message",
    "completed_at",
    "duration_seconds",
]


class AnalysisService:
    """Orchestrates the execution of analysis tasks."""

    MAX_WORKERS = 4

    def execute(self, task: AnalysisTask) -> None:
        """Run all configured analyzers for the given task."""
        _ensure_analyzers_registered()
        try:
            self._execute_inner(task)
        except Exception:
            logger.exception(
                "Unexpected error executing analysis task %s",
                task.id,
            )
            _set_task_failed(
                task,
                "Internal error during analysis execution.",
            )

    def _execute_inner(self, task: AnalysisTask) -> None:
        with transaction.atomic():
            task = AnalysisTask.objects.select_for_update().get(id=task.id)
            if task.status != AnalysisTask.Status.PENDING:
                logger.warning(
                    "Task %s is already %s, skipping execution",
                    task.id,
                    task.status,
                )
                return
            task.status = AnalysisTask.Status.RUNNING
            task.started_at = timezone.now()
            task.save(update_fields=["status", "started_at"])

        code = task.get_code_for_analysis()
        if not code:
            _set_task_failed(task, "No code available for analysis.")
            return

        analyzer_names: list[str] = task.configuration.get(
            "analyzers",
            [],
        )
        settings: dict[str, Any] = task.configuration.get(
            "settings",
            {},
        )

        if not analyzer_names:
            _set_task_failed(
                task,
                "No analyzers specified in configuration.",
            )
            return

        runnable = self._prepare_results(
            task,
            analyzer_names,
            settings,
        )
        self._run_all(runnable, code)
        self._finalize_task(task)

    def _prepare_results(
        self,
        task: AnalysisTask,
        analyzer_names: list[str],
        settings: dict[str, Any],
    ) -> list[tuple[AnalysisResult, BaseAnalyzer, dict[str, Any] | None]]:
        runnable: list[
            tuple[
                AnalysisResult,
                BaseAnalyzer,
                dict[str, Any] | None,
            ]
        ] = []
        for name in analyzer_names:
            analyzer = AnalyzerRegistry.get_instance(name)
            result_obj = AnalysisResult.objects.create(
                task=task,
                analyzer_name=name,
                analyzer_type=(analyzer.analyzer_type if analyzer else ""),
                status=AnalysisResult.Status.PENDING,
            )
            if analyzer is None:
                logger.warning(
                    "Analyzer %r not found, skipping",
                    name,
                )
                result_obj.status = AnalysisResult.Status.SKIPPED
                result_obj.error_message = f"Analyzer '{name}' is not registered."
                result_obj.save(
                    update_fields=["status", "error_message"],
                )
            else:
                runnable.append(
                    (result_obj, analyzer, settings.get(name)),
                )
        return runnable

    def _run_all(
        self,
        runnable: list[
            tuple[
                AnalysisResult,
                BaseAnalyzer,
                dict[str, Any] | None,
            ]
        ],
        code: dict[str, str],
    ) -> None:
        if not runnable:
            return
        workers = min(self.MAX_WORKERS, len(runnable))
        with ThreadPoolExecutor(max_workers=workers) as pool:
            futures = {
                pool.submit(
                    self._run_single_analyzer,
                    result_obj,
                    analyzer,
                    code,
                    config,
                ): result_obj
                for result_obj, analyzer, config in runnable
            }
            for future in as_completed(futures):
                result_obj = futures[future]
                exc = future.exception()
                if exc:
                    logger.error(
                        "Unhandled error running analyzer %s: %s",
                        result_obj.analyzer_name,
                        exc,
                    )
                    result_obj.status = AnalysisResult.Status.FAILED
                    result_obj.error_message = str(exc)
                    result_obj.completed_at = timezone.now()
                    if result_obj.started_at:
                        result_obj.duration_seconds = _compute_duration(
                            result_obj.started_at,
                            result_obj.completed_at,
                        )
                    result_obj.save(
                        update_fields=[
                            "status",
                            "error_message",
                            "completed_at",
                            "duration_seconds",
                        ],
                    )

    def _finalize_task(self, task: AnalysisTask) -> None:
        task.results_summary = self._aggregate_results(task)

        completed_count = task.results.filter(
            status=AnalysisResult.Status.COMPLETED,
        ).count()
        failed_count = task.results.filter(
            status=AnalysisResult.Status.FAILED,
        ).count()
        total = task.results.count()

        if completed_count == total:
            task.status = AnalysisTask.Status.COMPLETED
        elif failed_count == total:
            task.status = AnalysisTask.Status.FAILED
        else:
            task.status = AnalysisTask.Status.PARTIAL

        task.completed_at = timezone.now()
        if task.started_at:
            task.duration_seconds = _compute_duration(
                task.started_at,
                task.completed_at,
            )
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

    def _run_single_analyzer(
        self,
        result: AnalysisResult,
        analyzer: BaseAnalyzer,
        code: dict[str, str],
        config: dict[str, Any] | None,
    ) -> None:
        """Run one analyzer and persist its output."""
        result.status = AnalysisResult.Status.RUNNING
        result.started_at = timezone.now()
        result.save(update_fields=["status", "started_at"])

        try:
            output: AnalyzerOutput = analyzer.analyze(code, config)
        except Exception:
            logger.exception(
                "Analyzer %s raised an exception",
                analyzer.name,
            )
            result.status = AnalysisResult.Status.FAILED
            result.error_message = (
                f"Analyzer '{analyzer.name}' raised an unexpected error."
            )
            result.completed_at = timezone.now()
            result.duration_seconds = _compute_duration(
                result.started_at,
                result.completed_at,
            )
            result.save(update_fields=_RESULT_SAVE_FIELDS)
            return

        if output.has_error:
            result.status = AnalysisResult.Status.FAILED
            result.error_message = output.error or ""
        else:
            result.status = AnalysisResult.Status.COMPLETED
            count = self._save_findings(result, output.findings)
            logger.info(
                "Analyzer %s produced %d findings",
                analyzer.name,
                count,
            )

        result.raw_output = output.raw_output
        result.summary = output.summary
        result.completed_at = timezone.now()
        result.duration_seconds = _compute_duration(
            result.started_at,
            result.completed_at,
        )
        result.save(
            update_fields=[
                *_RESULT_SAVE_FIELDS,
                "raw_output",
                "summary",
            ],
        )

    def _save_findings(
        self,
        result: AnalysisResult,
        findings: list[FindingData],
    ) -> int:
        """Bulk-create Finding records. Returns count created."""
        if not findings:
            return 0

        objects = [
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
        with transaction.atomic():
            Finding.objects.bulk_create(objects)
        return len(objects)

    def _aggregate_results(
        self,
        task: AnalysisTask,
    ) -> dict[str, Any]:
        """Compute aggregate summary from all results."""
        results = task.results.all()
        all_findings = Finding.objects.filter(result__task=task)

        severity_counts = Counter(
            all_findings.values_list("severity", flat=True),
        )
        category_counts = Counter(
            all_findings.values_list("category", flat=True),
        )

        by_severity: dict[str, int] = {
            s.value: severity_counts.get(s.value, 0) for s in Finding.Severity
        }
        by_category: dict[str, int] = {
            c.value: category_counts.get(c.value, 0) for c in Finding.Category
        }

        completed = 0
        failed = 0
        by_analyzer: dict[str, dict[str, Any]] = {}
        for r in results:
            finding_count = r.findings.count()
            by_analyzer[r.analyzer_name] = {
                "status": r.status,
                "findings": finding_count,
                "duration": r.duration_seconds,
            }
            if r.status == AnalysisResult.Status.COMPLETED:
                completed += 1
            elif r.status == AnalysisResult.Status.FAILED:
                failed += 1

        return {
            "total_findings": all_findings.count(),
            "by_severity": by_severity,
            "by_category": by_category,
            "by_analyzer": by_analyzer,
            "analyzers_completed": completed,
            "analyzers_failed": failed,
            "analyzers_total": results.count(),
        }

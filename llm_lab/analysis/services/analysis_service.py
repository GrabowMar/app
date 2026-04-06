"""Thin orchestrator that coordinates analysis execution."""

from __future__ import annotations

import importlib
import logging
from typing import Any

from django.db import transaction
from django.utils import timezone

from llm_lab.analysis.models import AnalysisTask
from llm_lab.analysis.services.executor_service import ExecutorService
from llm_lab.analysis.services.result_service import ResultService

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


class AnalysisService:
    """Thin orchestrator that coordinates analysis execution."""

    def __init__(self) -> None:
        self.result_service = ResultService()
        self.executor_service = ExecutorService(self.result_service)

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

        runnable = self.result_service.create_results(
            task,
            analyzer_names,
            settings,
        )
        self.executor_service.run_all(runnable, code)
        self.result_service.finalize_task(task)

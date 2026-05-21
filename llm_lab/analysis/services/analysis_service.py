"""Thin orchestrator that coordinates analysis task execution."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING
from typing import Any

from django.db import transaction
from django.utils import timezone

from llm_lab.analysis.models import AnalysisTask
from llm_lab.analysis.services import cancellation
from llm_lab.analysis.services.executor_service import ExecutorService
from llm_lab.analysis.services.result_service import ResultService
from llm_lab.realtime import events as realtime

if TYPE_CHECKING:
    from llm_lab.runtime.models import ContainerInstance

logger = logging.getLogger(__name__)


def _set_task_failed(task: AnalysisTask, message: str) -> None:
    task.status = AnalysisTask.Status.FAILED
    task.error_message = message
    task.completed_at = timezone.now()
    if task.started_at:
        task.duration_seconds = (task.completed_at - task.started_at).total_seconds()
    task.save(
        update_fields=[
            "status",
            "error_message",
            "completed_at",
            "duration_seconds",
        ],
    )
    realtime.publish(
        f"analysis:{task.id}",
        {
            "type": "status",
            "status": task.status,
            "error_message": message,
            "updated_at": task.completed_at.isoformat() if task.completed_at else None,
        },
    )


class AnalysisService:
    """Thin orchestrator that coordinates analysis execution."""

    def __init__(self) -> None:
        self.result_service = ResultService()
        self.executor_service = ExecutorService(self.result_service)

    def execute(self, task: AnalysisTask) -> None:
        """Run all configured analyzers for the given task."""
        try:
            self._execute_inner(task)
        except Exception:
            logger.exception(
                "Unexpected error executing analysis task %s",
                task.id,
            )
            _set_task_failed(task, "Internal error during analysis execution.")

    def _execute_inner(self, task: AnalysisTask) -> None:
        # ── Atomic state transition ────────────────────────────────────────
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

        # Publish AFTER the transaction commits so listeners that poll the REST
        # API immediately on receiving this event see the updated status.
        realtime.publish(
            f"analysis:{task.id}",
            {
                "type": "status",
                "status": task.status,
                "updated_at": task.started_at.isoformat(),
            },
        )

        code = task.get_code_for_analysis()
        if not code:
            _set_task_failed(task, "No code available for analysis.")
            return

        analyzer_names: list[str] = task.configuration.get("analyzers", [])
        settings: dict[str, Any] = {
            k: dict(v) if isinstance(v, dict) else v
            for k, v in task.configuration.get("settings", {}).items()
        }

        if not analyzer_names:
            _set_task_failed(task, "No analyzers specified in configuration.")
            return

        if task.generation_job_id:
            app_requirement = getattr(task.generation_job, "app_requirement", None)
            for name in analyzer_names:
                analyzer_settings = settings.setdefault(name, {})
                if not isinstance(analyzer_settings, dict):
                    analyzer_settings = {}
                    settings[name] = analyzer_settings
                analyzer_settings.setdefault("generation_job_id", str(task.generation_job_id))
                if app_requirement is not None:
                    analyzer_settings.setdefault("app_requirement_id", app_requirement.id)
                    analyzer_settings.setdefault("app_requirement_slug", app_requirement.slug)

        # ── Live-target container orchestration ───────────────────────────
        live_target_enabled: bool = bool(task.configuration.get("live_target"))
        job_id: str | None = task.configuration.get("generation_job_id")
        container_instance: ContainerInstance | None = None

        # Register a cancellation token so the cancel API can stop this task.
        cancel = cancellation.register(str(task.id))

        try:
            if live_target_enabled and job_id:
                from llm_lab.analysis.services.live_target import prepare_live_target

                container_instance, target_url = prepare_live_target(task, job_id)
                for name in analyzer_names:
                    if name not in settings or not isinstance(settings[name], dict):
                        settings[name] = {}
                    settings[name]["target_url"] = target_url
                    settings[name]["live_target"] = True
                task.configuration["target_url"] = target_url
                task.save(update_fields=["configuration"])

            runnable = self.result_service.create_results(task, analyzer_names, settings)
            self.executor_service.run_all(runnable, code, cancel=cancel)
            self.result_service.finalize_task(task)

        finally:
            cancellation.release(str(task.id))
            if live_target_enabled and not task.configuration.get("keep_container"):
                if container_instance is None:
                    cid = task.configuration.get("container_instance_id")
                    if cid:
                        try:
                            from llm_lab.runtime.models import ContainerInstance

                            container_instance = ContainerInstance.objects.get(id=cid)
                        except Exception:  # noqa: BLE001
                            logger.warning(
                                "Could not retrieve container instance %s for teardown",
                                cid,
                            )
                if container_instance is not None:
                    from llm_lab.analysis.services.live_target import teardown_live_target

                    teardown_live_target(container_instance)

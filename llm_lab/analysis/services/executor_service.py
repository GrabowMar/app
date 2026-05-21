"""Manages parallel analyzer execution via a shared global thread pool."""

from __future__ import annotations

import atexit
import logging
import threading
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import as_completed
from typing import TYPE_CHECKING
from typing import Any

from django.conf import settings
from django.utils import timezone

from llm_lab.analysis.models import AnalysisResult

if TYPE_CHECKING:
    from llm_lab.analysis.services.base import AnalyzerOutput
    from llm_lab.analysis.services.base import BaseAnalyzer
    from llm_lab.analysis.services.cancellation import CancellationToken
    from llm_lab.analysis.services.result_service import ResultService

logger = logging.getLogger(__name__)

# ── Global pool ───────────────────────────────────────────────────────────────
# A single process-wide pool shared across all concurrent analysis tasks.
# Configure the ceiling via settings.ANALYZER_MAX_WORKERS (default 8).

_POOL: ThreadPoolExecutor | None = None
_POOL_LOCK = threading.Lock()


def _get_pool() -> ThreadPoolExecutor:
    global _POOL  # noqa: PLW0603
    if _POOL is None:
        with _POOL_LOCK:
            if _POOL is None:
                max_workers = getattr(settings, "ANALYZER_MAX_WORKERS", 8)
                _POOL = ThreadPoolExecutor(
                    max_workers=max_workers,
                    thread_name_prefix="analyzer",
                )
                atexit.register(_POOL.shutdown, wait=False)
    return _POOL


# ── Service ───────────────────────────────────────────────────────────────────


class ExecutorService:
    """Dispatches analyzer runs to the global thread pool."""

    def __init__(self, result_service: ResultService) -> None:
        self.result_service = result_service

    def run_all(
        self,
        runnable: list[
            tuple[
                AnalysisResult,
                BaseAnalyzer,
                dict[str, Any] | None,
            ]
        ],
        code: dict[str, str],
        cancel: CancellationToken | None = None,
    ) -> None:
        """Submit all analyzers to the global pool and wait for completion.

        Analyzers are submitted in descending priority order so that
        higher-priority work enters the pool queue first.
        """
        if not runnable:
            return

        # Sort by priority descending (higher value = submitted first).
        ordered = sorted(runnable, key=lambda t: t[1].priority, reverse=True)

        pool = _get_pool()
        futures = {
            pool.submit(
                self._run_single,
                result_obj,
                analyzer,
                code,
                config,
                cancel,
            ): result_obj
            for result_obj, analyzer, config in ordered
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
                self.result_service.mark_result_failed(result_obj, str(exc))

    def _run_single(
        self,
        result: AnalysisResult,
        analyzer: BaseAnalyzer,
        code: dict[str, str],
        config: dict[str, Any] | None,
        cancel: CancellationToken | None,
    ) -> None:
        """Run one analyzer and persist its output.  Called from pool threads."""
        # Bail before doing any work if the task has already been cancelled.
        if cancel is not None and cancel.is_cancelled():
            self.result_service.mark_result_cancelled(result)
            return

        result.status = AnalysisResult.Status.RUNNING
        result.started_at = timezone.now()
        result.save(update_fields=["status", "started_at"])

        try:
            output: AnalyzerOutput = analyzer.analyze(code, config, cancel=cancel)
        except Exception:
            logger.exception("Analyzer %s raised an exception", analyzer.name)
            self.result_service.mark_result_failed(
                result,
                f"Analyzer '{analyzer.name}' raised an unexpected error.",
            )
            return

        # The analyzer returned, but the task may have been cancelled while it
        # was running (e.g. subprocess was killed).
        if cancel is not None and cancel.is_cancelled():
            self.result_service.mark_result_cancelled(result)
            return

        self.result_service.save_analyzer_output(result, output, analyzer)

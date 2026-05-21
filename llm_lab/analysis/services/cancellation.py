"""Task-scoped cancellation tokens for in-flight analyzer runs."""

from __future__ import annotations

import logging
import subprocess
import threading

logger = logging.getLogger(__name__)

# ── Token ─────────────────────────────────────────────────────────────────────


class CancellationToken:
    """Cooperative cancellation signal for a single analysis task.

    Analyzers register their active subprocesses so they can be terminated
    immediately when cancel() is called. Thread-safe.
    """

    __slots__ = ("_event", "_lock", "_processes")

    def __init__(self) -> None:
        self._event = threading.Event()
        self._lock = threading.Lock()
        self._processes: list[subprocess.Popen] = []

    # -- Public API --------------------------------------------------------

    def cancel(self) -> None:
        """Signal cancellation and terminate any registered subprocesses."""
        self._event.set()
        with self._lock:
            for proc in self._processes:
                try:
                    if proc.poll() is None:
                        proc.terminate()
                except OSError:
                    pass

    def is_cancelled(self) -> bool:
        return self._event.is_set()

    def register_process(self, proc: subprocess.Popen) -> None:
        """Register a subprocess so it is terminated on cancel().

        If cancellation has already been requested the process is terminated
        immediately.
        """
        with self._lock:
            self._processes.append(proc)
            if self._event.is_set():
                try:
                    if proc.poll() is None:
                        proc.terminate()
                except OSError:
                    pass


# ── Registry ──────────────────────────────────────────────────────────────────

_registry: dict[str, CancellationToken] = {}
_lock = threading.Lock()


def register(task_id: str) -> CancellationToken:
    """Create and register a token for *task_id*. Returns the token."""
    token = CancellationToken()
    with _lock:
        _registry[str(task_id)] = token
    return token


def request_cancellation(task_id: str) -> bool:
    """Signal cancellation for *task_id*.

    Returns True if a token was found and cancelled, False if the task is not
    currently executing (already finished or not started yet).
    """
    with _lock:
        token = _registry.get(str(task_id))
    if token is None:
        return False
    token.cancel()
    logger.debug("Cancellation requested for task %s", task_id)
    return True


def release(task_id: str) -> None:
    """Remove the token for *task_id* from the registry after execution ends."""
    with _lock:
        _registry.pop(str(task_id), None)

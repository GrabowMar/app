"""Base analyzer framework — ABC, dataclasses, registry, and shared utilities."""

from __future__ import annotations

import contextlib
import json
import logging
import re
import subprocess
import tempfile
import threading
from abc import ABC
from abc import abstractmethod
from collections.abc import Iterator
from dataclasses import dataclass
from dataclasses import field
from pathlib import Path
from typing import TYPE_CHECKING
from typing import Any
from typing import ClassVar

from llm_lab.common.security import validate_target_url  # re-export

if TYPE_CHECKING:
    from llm_lab.analysis.services.cancellation import CancellationToken

__all__ = [
    "validate_target_url",
]

logger = logging.getLogger(__name__)


# ── Utilities ─────────────────────────────────────────────────────────────────


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except (ValueError, TypeError):
        return default


def _extract_code(code: dict[str, str], key: str, extensions: set[str]) -> str:
    """Extract code from a code dict that may use semantic keys or filenames."""
    if key in code and code[key].strip():
        return code[key]
    parts: list[str] = []
    for filename, content in code.items():
        if not content or not content.strip():
            continue
        ext = Path(filename).suffix.lower() if "." in filename else ""
        if ext in extensions:
            parts.append(f"# --- {filename} ---\n{content}")
    return "\n\n".join(parts)


def build_severity_counts(findings: list[FindingData]) -> dict[str, int]:
    counts: dict[str, int] = {
        "critical": 0,
        "high": 0,
        "medium": 0,
        "low": 0,
        "info": 0,
    }
    for f in findings:
        if f.severity in counts:
            counts[f.severity] += 1
    return counts


def run_subprocess(
    cmd: list[str],
    *,
    timeout: int = 60,
    cancel: CancellationToken | None = None,
    cwd: str | Path | None = None,
) -> subprocess.CompletedProcess[str] | None:
    """Run *cmd* in a subprocess, registering it with *cancel* if provided.

    Returns a :class:`subprocess.CompletedProcess` on success, or ``None``
    when the process times out or cancellation is requested.  Callers should
    check ``cancel.is_cancelled()`` to distinguish the two cases.
    """
    proc = subprocess.Popen(  # noqa: S603
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        cwd=str(cwd) if cwd is not None else None,
    )
    if cancel is not None:
        cancel.register_process(proc)
    try:
        stdout, stderr = proc.communicate(timeout=timeout)
    except subprocess.TimeoutExpired:
        proc.kill()
        proc.communicate()  # drain pipes
        return None
    # The process may have been terminated by cancel() after communicate() returned.
    if cancel is not None and cancel.is_cancelled():
        return None
    return subprocess.CompletedProcess(cmd, proc.returncode, stdout, stderr)


def check_cli(
    cmd: list[str],
    *,
    tool_name: str | None = None,
    timeout: int = 15,
    success_codes: set[int] | None = None,
) -> tuple[bool, str]:
    """Return availability for a CLI based on a lightweight version/help command."""
    if not cmd:
        return False, "Invalid command"
    binary = tool_name or cmd[0]
    allowed = success_codes or {0}
    try:
        result = subprocess.run(  # noqa: S603
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
    except FileNotFoundError:
        return False, f"{binary} is not installed"
    except subprocess.TimeoutExpired:
        return False, f"{binary} check timed out"

    output = (result.stdout or result.stderr).strip()
    if result.returncode in allowed:
        first_line = output.splitlines()[0].strip() if output else ""
        return True, first_line or "Available"
    if output:
        return False, output.splitlines()[0].strip()
    return False, f"{binary} is not available"


def _looks_like_path(label: str) -> bool:
    return "/" in label or "\\" in label or Path(label).suffix != ""


def _guess_filename(label: str, content: str) -> Path:  # noqa: PLR0911
    if _looks_like_path(label):
        return Path(label)

    lower_label = label.lower()
    lower_content = content.lower()
    if lower_label == "backend":
        return Path("backend/app.py")
    if lower_label == "frontend":
        if "<!doctype html" in lower_content or "<html" in lower_content:
            return Path("frontend/index.html")
        if "<script" in lower_content and "<style" in lower_content:
            return Path("frontend/src/App.svelte")
        if re.search(r"\binterface\s+\w+|\btype\s+\w+\s*=", content):
            return Path("frontend/src/App.tsx")
        if re.search(r"\bexport\s+default\b|\buseState\b|<[A-Z][A-Za-z0-9_]*", content):
            return Path("frontend/src/App.jsx")
        if re.search(r"{[^}]+:[^}]+;|\.[A-Za-z0-9_-]+\s*\{", content):
            return Path("frontend/src/app.css")
        return Path("frontend/src/app.js")
    return Path(f"{lower_label or 'code'}.txt")


def _write_code_tree(root: Path, code: dict[str, str]) -> None:
    from llm_lab.generation.services.code_parser import infer_python_dependencies
    from llm_lab.runtime.services.scaffolding_engine.engine import _extract_js_imports

    backend_source = ""
    frontend_source = ""

    for label, content in code.items():
        if not content or not content.strip():
            continue
        rel_path = _guess_filename(label, content)
        dest = root / rel_path
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(content)
        if label.lower() == "backend":
            backend_source = content
        if label.lower() == "frontend":
            frontend_source = content

    if backend_source:
        requirements_path = root / "backend" / "requirements.txt"
        if not requirements_path.exists():
            deps = infer_python_dependencies(backend_source)
            if deps:
                requirements_path.parent.mkdir(parents=True, exist_ok=True)
                requirements_path.write_text("\n".join(deps) + "\n")

    if frontend_source:
        package_json = root / "frontend" / "package.json"
        if not package_json.exists():
            dependencies = dict.fromkeys(_extract_js_imports(frontend_source), "*")
            package_json.parent.mkdir(parents=True, exist_ok=True)
            package_json.write_text(
                "{\n"
                '  "name": "analysis-frontend",\n'
                '  "private": true,\n'
                '  "dependencies": '
                f"{json.dumps(dict(sorted(dependencies.items())), indent=2)}\n"
                "}\n",
            )


@contextlib.contextmanager
def materialize_analysis_project(
    code: dict[str, str],
    *,
    config: dict[str, Any] | None = None,
) -> Iterator[Path]:
    """Materialize analysis inputs into a temporary project tree."""
    from llm_lab.runtime.services.scaffolding import prepare_build_dir

    with tempfile.TemporaryDirectory(prefix="analysis-project-") as tmpdir:
        root = Path(tmpdir)
        generation_job_id = (config or {}).get("generation_job_id")
        if generation_job_id:
            with contextlib.suppress(Exception):
                from llm_lab.generation.models import GenerationJob

                job = GenerationJob.objects.select_related("scaffolding_template").get(id=generation_job_id)
                prepare_build_dir(job, root)
                yield root
                return
        _write_code_tree(root, code)
        yield root


# ── Data classes ──────────────────────────────────────────────────────────────


@dataclass
class FindingData:
    """Normalized finding from any analyzer tool."""

    severity: str  # critical, high, medium, low, info
    category: str  # security, quality, performance, style, best_practice, …
    title: str
    description: str = ""
    suggestion: str = ""
    file_path: str = ""
    line_number: int | None = None
    column_number: int | None = None
    code_snippet: str = ""
    rule_id: str = ""
    confidence: str = "medium"  # high, medium, low
    tool_specific_data: dict[str, Any] = field(default_factory=dict)


@dataclass
class AnalyzerOutput:
    """Standard output from an analyzer run."""

    findings: list[FindingData] = field(default_factory=list)
    summary: dict[str, Any] = field(default_factory=dict)
    raw_output: dict[str, Any] = field(default_factory=dict)
    error: str | None = None

    @property
    def has_error(self) -> bool:
        return self.error is not None

    @property
    def finding_counts(self) -> dict[str, int]:
        counts: dict[str, int] = {
            "critical": 0,
            "high": 0,
            "medium": 0,
            "low": 0,
            "info": 0,
        }
        for f in self.findings:
            if f.severity in counts:
                counts[f.severity] += 1
        return counts


# ── Base analyzer ─────────────────────────────────────────────────────────────


class BaseAnalyzer(ABC):
    """Abstract base class for all analyzers.

    To create a new analyzer:
    1. Subclass BaseAnalyzer.
    2. Set ``name``, ``analyzer_type``, ``display_name``, and ``description``.
    3. Implement ``analyze(code, config, *, cancel)``.
    4. The class is auto-registered via ``__init_subclass__``.

    Class variables
    ---------------
    default_timeout : int
        Seconds before a subprocess run is forcibly killed (default 60).
        Individual tasks can override this via the ``timeout`` config key.
    priority : int
        Scheduling priority within a task (1 = lowest, 10 = highest, default 5).
        Higher-priority analyzers are submitted to the pool first.
    """

    name: ClassVar[str]
    analyzer_type: ClassVar[str]
    display_name: ClassVar[str]
    description: ClassVar[str] = ""
    default_config: ClassVar[dict[str, Any]] = {}
    default_timeout: ClassVar[int] = 60
    priority: ClassVar[int] = 5

    def __init__(self) -> None:
        # Cached result of check_available() — set on first call.
        self._availability: tuple[bool, str] | None = None

    def __init_subclass__(cls, **kwargs: Any) -> None:
        super().__init_subclass__(**kwargs)
        if hasattr(cls, "name") and hasattr(cls, "analyzer_type"):
            AnalyzerRegistry.register(cls)

    # -- Abstract interface ------------------------------------------------

    @abstractmethod
    def analyze(
        self,
        code: dict[str, str],
        config: dict[str, Any] | None = None,
        *,
        cancel: CancellationToken | None = None,
    ) -> AnalyzerOutput:
        """Run analysis on the provided code.

        Parameters
        ----------
        code:
            Dict mapping file type/name to code content.
            e.g. ``{"backend": "...", "frontend": "..."}``.
        config:
            Optional analyzer-specific configuration.  Recognised keys
            vary by analyzer; see each implementation's ``default_config``.
        cancel:
            Optional :class:`~cancellation.CancellationToken`.  Analyzers
            that spawn subprocesses should pass it to :func:`run_subprocess`
            so the process is terminated immediately on cancellation.
        """

    # -- Availability ------------------------------------------------------

    def check_available(self) -> tuple[bool, str]:
        """Check whether this analyzer's dependencies are installed.

        The result is cached after the first call (per instance, which are
        themselves cached in :class:`AnalyzerRegistry`).
        """
        return True, "Available"

    def get_availability(self) -> tuple[bool, str]:
        """Return cached availability, calling ``check_available()`` once."""
        if self._availability is None:
            self._availability = self.check_available()
        return self._availability

    # -- Metadata ----------------------------------------------------------

    def get_info(self) -> dict[str, Any]:
        available, message = self.get_availability()
        return {
            "name": self.name,
            "type": self.analyzer_type,
            "display_name": self.display_name,
            "description": self.description,
            "available": available,
            "availability_message": message,
            "default_config": self.default_config,
            "default_timeout": self.default_timeout,
            "priority": self.priority,
        }


# ── Registry ──────────────────────────────────────────────────────────────────


class AnalyzerRegistry:
    """Singleton registry for all analyzer classes.

    Instances are cached — each analyzer class is instantiated exactly once so
    that ``get_availability()`` results are shared across all callers.
    """

    _analyzers: ClassVar[dict[str, type[BaseAnalyzer]]] = {}
    _instances: ClassVar[dict[str, BaseAnalyzer]] = {}
    _lock: ClassVar[threading.Lock] = threading.Lock()

    @classmethod
    def register(cls, analyzer_cls: type[BaseAnalyzer]) -> None:
        name = analyzer_cls.name
        with cls._lock:
            if name in cls._analyzers:
                logger.debug("Overriding analyzer registration: %s", name)
            cls._analyzers[name] = analyzer_cls
            # Invalidate any cached instance for this name.
            cls._instances.pop(name, None)
        logger.debug("Registered analyzer: %s (%s)", name, analyzer_cls.analyzer_type)

    @classmethod
    def get(cls, name: str) -> type[BaseAnalyzer] | None:
        return cls._analyzers.get(name)

    @classmethod
    def get_instance(cls, name: str) -> BaseAnalyzer | None:
        """Return a cached analyzer instance, creating it on first access."""
        with cls._lock:
            if name not in cls._instances:
                analyzer_cls = cls._analyzers.get(name)
                if analyzer_cls is None:
                    return None
                cls._instances[name] = analyzer_cls()
            return cls._instances[name]

    @classmethod
    def list_available(cls) -> list[dict[str, Any]]:
        result = []
        with cls._lock:
            names = sorted(cls._analyzers.keys())
        for name in names:
            instance = cls.get_instance(name)
            if instance is not None:
                result.append(instance.get_info())
        return result

    @classmethod
    def list_by_type(cls, analyzer_type: str) -> list[dict[str, Any]]:
        return [info for info in cls.list_available() if info["type"] == analyzer_type]

    @classmethod
    def list_names(cls) -> list[str]:
        return sorted(cls._analyzers.keys())

    @classmethod
    def clear(cls) -> None:
        """Clear registry (for testing)."""
        with cls._lock:
            cls._analyzers.clear()
            cls._instances.clear()

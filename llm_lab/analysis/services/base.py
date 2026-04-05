"""Base analyzer framework — ABC, dataclasses, and registry."""

from __future__ import annotations

import logging
from abc import ABC
from abc import abstractmethod
from dataclasses import dataclass
from dataclasses import field
from typing import Any
from typing import ClassVar

logger = logging.getLogger(__name__)


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


class BaseAnalyzer(ABC):
    """Abstract base class for all analyzers.

    To create a new analyzer:
    1. Subclass BaseAnalyzer
    2. Set `name`, `analyzer_type`, `display_name`, `description`
    3. Implement `analyze(code, config)` method
    4. The class is auto-registered via __init_subclass__
    """

    name: ClassVar[str]  # e.g. "bandit", "eslint"
    analyzer_type: ClassVar[str]  # "static", "dynamic", "performance", "ai"
    display_name: ClassVar[str]  # "Bandit Security Scanner"
    description: ClassVar[str] = ""
    default_config: ClassVar[dict[str, Any]] = {}

    def __init_subclass__(cls, **kwargs: Any) -> None:
        super().__init_subclass__(**kwargs)
        # Auto-register concrete subclasses
        if hasattr(cls, "name") and hasattr(cls, "analyzer_type"):
            AnalyzerRegistry.register(cls)

    @abstractmethod
    def analyze(
        self,
        code: dict[str, str],
        config: dict[str, Any] | None = None,
    ) -> AnalyzerOutput:
        """Run analysis on the provided code.

        Args:
            code: Dict mapping file type/name to code content.
                  e.g. {"backend": "...", "frontend": "..."}
            config: Optional analyzer-specific configuration.

        Returns:
            AnalyzerOutput with findings, summary, and raw output.
        """

    def check_available(self) -> tuple[bool, str]:
        """Check if this analyzer's dependencies are available.

        Returns:
            Tuple of (available, message).
        """
        return True, "Available"

    def get_info(self) -> dict[str, Any]:
        """Return metadata about this analyzer."""
        available, message = self.check_available()
        return {
            "name": self.name,
            "type": self.analyzer_type,
            "display_name": self.display_name,
            "description": self.description,
            "available": available,
            "availability_message": message,
            "default_config": self.default_config,
        }


class AnalyzerRegistry:
    """Singleton registry for all analyzer classes."""

    _analyzers: ClassVar[dict[str, type[BaseAnalyzer]]] = {}

    @classmethod
    def register(cls, analyzer_cls: type[BaseAnalyzer]) -> None:
        name = analyzer_cls.name
        if name in cls._analyzers:
            logger.debug("Overriding analyzer registration: %s", name)
        cls._analyzers[name] = analyzer_cls
        logger.debug("Registered analyzer: %s (%s)", name, analyzer_cls.analyzer_type)

    @classmethod
    def get(cls, name: str) -> type[BaseAnalyzer] | None:
        return cls._analyzers.get(name)

    @classmethod
    def get_instance(cls, name: str) -> BaseAnalyzer | None:
        analyzer_cls = cls.get(name)
        if analyzer_cls is None:
            return None
        return analyzer_cls()

    @classmethod
    def list_available(cls) -> list[dict[str, Any]]:
        result = []
        for analyzer_cls in cls._analyzers.values():
            instance = analyzer_cls()
            result.append(instance.get_info())
        return result

    @classmethod
    def list_by_type(cls, analyzer_type: str) -> list[dict[str, Any]]:
        return [
            info
            for info in cls.list_available()
            if info["type"] == analyzer_type
        ]

    @classmethod
    def list_names(cls) -> list[str]:
        return sorted(cls._analyzers.keys())

    @classmethod
    def clear(cls) -> None:
        """Clear registry (for testing)."""
        cls._analyzers.clear()

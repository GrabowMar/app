"""Python-based performance analyzers aligned with the legacy tool inventory."""

from __future__ import annotations

import asyncio
import math
import statistics
import time
from importlib.util import find_spec
from typing import TYPE_CHECKING
from typing import Any
from typing import ClassVar

from llm_lab.analysis.services.base import AnalyzerOutput
from llm_lab.analysis.services.base import BaseAnalyzer
from llm_lab.analysis.services.base import FindingData
from llm_lab.analysis.services.live_target import resolve_target_url

if TYPE_CHECKING:
    from llm_lab.analysis.services.cancellation import CancellationToken


def _parse_duration(value: str) -> int:
    if not value:
        return 30
    suffix = value[-1]
    number = int(value[:-1]) if value[:-1].isdigit() else 30
    if suffix == "h":
        return number * 3600
    if suffix == "m":
        return number * 60
    return number


def _percentile(values: list[float], percentile: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    index = min(len(ordered) - 1, max(0, math.ceil(percentile * len(ordered)) - 1))
    return round(ordered[index], 2)


async def _request_once(
    session,
    url: str,
    *,
    timeout_seconds: int,
) -> tuple[int | None, float, str | None]:
    import aiohttp

    started = time.perf_counter()
    try:
        async with session.get(url, timeout=aiohttp.ClientTimeout(total=timeout_seconds)) as response:
            await response.read()
            duration_ms = round((time.perf_counter() - started) * 1000, 2)
            return response.status, duration_ms, None
    except Exception as exc:  # noqa: BLE001
        duration_ms = round((time.perf_counter() - started) * 1000, 2)
        return None, duration_ms, str(exc)


async def _run_load_test(
    url: str,
    *,
    total_requests: int,
    concurrency: int,
    timeout_seconds: int,
    cancel: CancellationToken | None = None,
) -> dict[str, Any]:
    import aiohttp

    if total_requests <= 0:
        return {
            "statuses": [],
            "latencies_ms": [],
            "errors": [],
            "total_requests": 0,
        }

    semaphore = asyncio.Semaphore(max(1, concurrency))
    statuses: list[int | None] = []
    latencies_ms: list[float] = []
    errors: list[str] = []

    async with aiohttp.ClientSession() as session:
        async def _worker() -> None:
            async with semaphore:
                if cancel is not None and cancel.is_cancelled():
                    return
                status, latency_ms, error = await _request_once(
                    session,
                    url,
                    timeout_seconds=timeout_seconds,
                )
                statuses.append(status)
                latencies_ms.append(latency_ms)
                if error:
                    errors.append(error)

        await asyncio.gather(*[_worker() for _ in range(total_requests)])

    return {
        "statuses": statuses,
        "latencies_ms": latencies_ms,
        "errors": errors,
        "total_requests": total_requests,
    }


def _build_output(tool_name: str, metrics: dict[str, Any], *, config: dict[str, Any]) -> AnalyzerOutput:
    total_requests = int(metrics["total_requests"])
    latencies = list(metrics["latencies_ms"])
    errors = list(metrics["errors"])
    statuses = list(metrics["statuses"])
    successes = sum(1 for status in statuses if status is not None and 200 <= status < 400)
    failures = total_requests - successes
    avg_response = round(statistics.mean(latencies), 2) if latencies else 0.0
    p95 = _percentile(latencies, 0.95)
    max_response = round(max(latencies), 2) if latencies else 0.0
    failure_rate = round((failures / total_requests) * 100, 2) if total_requests else 0.0
    requests_per_second = round(total_requests / max(sum(latencies) / 1000, 0.001), 2) if latencies else 0.0

    findings: list[FindingData] = []
    if failure_rate >= 10:
        findings.append(
            FindingData(
                severity="high",
                category="performance",
                title=f"{tool_name} observed a high failure rate",
                description=f"{failure_rate}% of requests failed during the load test.",
                suggestion="Inspect server errors and reduce concurrency bottlenecks before rerunning the test.",
                rule_id=f"{tool_name}/failure-rate",
                confidence="high",
            ),
        )
    elif failure_rate > 0:
        findings.append(
            FindingData(
                severity="medium",
                category="performance",
                title=f"{tool_name} observed request failures",
                description=f"{failure_rate}% of requests failed during the load test.",
                suggestion="Review the failing endpoints and improve resilience under concurrent load.",
                rule_id=f"{tool_name}/failure-rate",
                confidence="high",
            ),
        )

    if avg_response >= 1000:
        findings.append(
            FindingData(
                severity="medium",
                category="performance",
                title=f"{tool_name} average response time is high",
                description=f"Average response time was {avg_response} ms.",
                suggestion="Profile slow handlers and optimize the main request path.",
                rule_id=f"{tool_name}/avg-response",
                confidence="medium",
            ),
        )
    if p95 >= 2000:
        findings.append(
            FindingData(
                severity="high" if p95 >= 4000 else "medium",
                category="performance",
                title=f"{tool_name} p95 latency is elevated",
                description=f"95th percentile response time was {p95} ms.",
                suggestion="Reduce tail latency by optimizing slow queries or expensive cold-start work.",
                rule_id=f"{tool_name}/p95-latency",
                confidence="medium",
            ),
        )

    return AnalyzerOutput(
        findings=findings,
        summary={
            "total_requests": total_requests,
            "successful_requests": successes,
            "failed_requests": failures,
            "failure_rate_percent": failure_rate,
            "average_response_time_ms": avg_response,
            "p95_response_time_ms": p95,
            "max_response_time_ms": max_response,
            "requests_per_second": requests_per_second,
            "configuration": config,
        },
        raw_output={"errors": errors[:50], "statuses": statuses[:100]},
    )


class _BasePythonLoadAnalyzer(BaseAnalyzer):
    default_timeout: ClassVar[int] = 180

    def check_available(self) -> tuple[bool, str]:
        if find_spec("aiohttp") is None:
            return False, "aiohttp is not installed"
        return True, "Available (uses Python aiohttp load testing)"

    def _run(
        self,
        url: str,
        *,
        total_requests: int,
        concurrency: int,
        timeout_seconds: int,
        config: dict[str, Any],
        cancel: CancellationToken | None = None,
    ) -> AnalyzerOutput:
        available, message = self.get_availability()
        if not available:
            return AnalyzerOutput(error=message)
        if cancel is not None and cancel.is_cancelled():
            return AnalyzerOutput(error="Analysis cancelled")
        metrics = asyncio.run(
            _run_load_test(
                url,
                total_requests=total_requests,
                concurrency=concurrency,
                timeout_seconds=timeout_seconds,
                cancel=cancel,
            ),
        )
        return _build_output(self.name, metrics, config=config)


class AiohttpLoadTestAnalyzer(_BasePythonLoadAnalyzer):
    name: ClassVar[str] = "aiohttp"
    analyzer_type: ClassVar[str] = "performance"
    display_name: ClassVar[str] = "aiohttp Load Test"
    description: ClassVar[str] = "Async HTTP load testing against a live target"
    default_config: ClassVar[dict[str, Any]] = {
        "requests": 50,
        "concurrency": 5,
        "timeout": 30,
    }

    def analyze(
        self,
        code: dict[str, str],
        config: dict[str, Any] | None = None,
        *,
        cancel: CancellationToken | None = None,
    ) -> AnalyzerOutput:
        del code
        merged = {**self.default_config, **(config or {})}
        target_url, error = resolve_target_url(merged)
        if error:
            return AnalyzerOutput(error=f"aiohttp load testing requires a live target: {error}")
        return self._run(
            target_url,
            total_requests=int(merged["requests"]),
            concurrency=int(merged["concurrency"]),
            timeout_seconds=int(merged["timeout"]),
            config=merged,
            cancel=cancel,
        )


class ApacheBenchAnalyzer(_BasePythonLoadAnalyzer):
    name: ClassVar[str] = "ab"
    analyzer_type: ClassVar[str] = "performance"
    display_name: ClassVar[str] = "Apache Bench"
    description: ClassVar[str] = "Simple burst-style HTTP load testing"
    default_config: ClassVar[dict[str, Any]] = {
        "requests": 100,
        "concurrency": 10,
        "timeout": 30,
    }

    def analyze(
        self,
        code: dict[str, str],
        config: dict[str, Any] | None = None,
        *,
        cancel: CancellationToken | None = None,
    ) -> AnalyzerOutput:
        del code
        merged = {**self.default_config, **(config or {})}
        target_url, error = resolve_target_url(merged)
        if error:
            return AnalyzerOutput(error=f"Apache Bench requires a live target: {error}")
        return self._run(
            target_url,
            total_requests=int(merged["requests"]),
            concurrency=int(merged["concurrency"]),
            timeout_seconds=int(merged["timeout"]),
            config=merged,
            cancel=cancel,
        )


class LocustAnalyzer(_BasePythonLoadAnalyzer):
    name: ClassVar[str] = "locust"
    analyzer_type: ClassVar[str] = "performance"
    display_name: ClassVar[str] = "Locust Load Testing"
    description: ClassVar[str] = "User-oriented load testing with sustained concurrency"
    default_config: ClassVar[dict[str, Any]] = {
        "users": 50,
        "spawn_rate": 2.0,
        "run_time": "30s",
        "timeout": 30,
    }

    def analyze(
        self,
        code: dict[str, str],
        config: dict[str, Any] | None = None,
        *,
        cancel: CancellationToken | None = None,
    ) -> AnalyzerOutput:
        del code
        merged = {**self.default_config, **(config or {})}
        target_url, error = resolve_target_url(merged)
        if error:
            return AnalyzerOutput(error=f"Locust requires a live target: {error}")

        duration_seconds = _parse_duration(str(merged["run_time"]))
        users = int(merged["users"])
        spawn_rate = max(float(merged["spawn_rate"]), 0.1)
        concurrency = max(1, min(users, math.ceil(users / spawn_rate)))
        total_requests = max(users, duration_seconds * max(1, math.ceil(spawn_rate)))
        return self._run(
            target_url,
            total_requests=total_requests,
            concurrency=concurrency,
            timeout_seconds=int(merged["timeout"]),
            config={**merged, "derived_total_requests": total_requests},
            cancel=cancel,
        )


class ArtilleryAnalyzer(_BasePythonLoadAnalyzer):
    name: ClassVar[str] = "artillery"
    analyzer_type: ClassVar[str] = "performance"
    display_name: ClassVar[str] = "Artillery Load Testing"
    description: ClassVar[str] = "Phased arrival-rate load testing"
    default_config: ClassVar[dict[str, Any]] = {
        "duration": 60,
        "arrival_rate": 10,
        "timeout": 10,
    }

    def analyze(
        self,
        code: dict[str, str],
        config: dict[str, Any] | None = None,
        *,
        cancel: CancellationToken | None = None,
    ) -> AnalyzerOutput:
        del code
        merged = {**self.default_config, **(config or {})}
        target_url, error = resolve_target_url(merged)
        if error:
            return AnalyzerOutput(error=f"Artillery requires a live target: {error}")

        phases = merged.get("phases")
        if isinstance(phases, list) and phases:
            total_requests = 0
            concurrency = 1
            for phase in phases:
                if not isinstance(phase, dict):
                    continue
                duration = int(phase.get("duration", 0))
                arrival_rate = int(phase.get("arrivalRate", phase.get("arrival_rate", 0)))
                total_requests += duration * max(arrival_rate, 1)
                concurrency = max(concurrency, arrival_rate)
        else:
            duration = int(merged["duration"])
            arrival_rate = int(merged["arrival_rate"])
            total_requests = duration * max(arrival_rate, 1)
            concurrency = max(1, arrival_rate)

        return self._run(
            target_url,
            total_requests=total_requests,
            concurrency=concurrency,
            timeout_seconds=int(merged["timeout"]),
            config={**merged, "derived_total_requests": total_requests},
            cancel=cancel,
        )

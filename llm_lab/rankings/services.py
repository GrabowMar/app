"""Rankings service — composite Model Selection Score (MSS).

Ported from the legacy `ModelRankingsService` (Flask app). The legacy service
fetched scores from external benchmarks (HuggingFace EvalPlus, SWE-Bench,
BigCodeBench, LiveBench, LiveCodeBench, OpenRouter rankings); here we read
benchmark scores from the `BenchmarkResult` table (seeded via the
``seed_benchmarks`` management command or admin) and combine them with
locally computed per-model adoption metrics from the existing GenerationJob
and Finding tables.

Composite formula (Chapter 4 methodology):

    MSS = 0.35*adoption + 0.30*benchmarks + 0.20*cost_efficiency
        + 0.15*accessibility
"""

from __future__ import annotations

import math
from typing import Any

from django.db.models import Avg
from django.db.models import Count
from django.db.models import Q

from llm_lab.analysis.models import Finding
from llm_lab.generation.models import GenerationJob
from llm_lab.llm_models.models import LLMModel
from llm_lab.rankings.models import BenchmarkResult

BENCHMARK_RANGES = {
    "bfcl_score": (0, 100),
    "webdev_elo": (800, 1400),
    "livebench_coding": (0, 100),
    "livecodebench": (0, 100),
    "arc_agi_score": (0, 100),
    "simplebench_score": (0, 100),
    "canaicode_score": (0, 100),
    "seal_coding_score": (800, 1400),
    "gpqa_score": (0, 100),
    "humaneval": (0, 100),
    "mbpp": (0, 100),
    "swebench": (0, 100),
}

BENCHMARK_WEIGHTS = {
    "bfcl_score": 0.12,
    "webdev_elo": 0.12,
    "livebench_coding": 0.08,
    "livecodebench": 0.08,
    "arc_agi_score": 0.08,
    "simplebench_score": 0.08,
    "canaicode_score": 0.08,
    "seal_coding_score": 0.08,
    "gpqa_score": 0.08,
    "humaneval": 0.08,
    "mbpp": 0.06,
    "swebench": 0.06,
}

LICENSE_SCORES = {
    "apache": 1.0, "mit": 1.0, "bsd": 1.0, "cc-by": 1.0,
    "llama": 0.7, "gemma": 0.7, "yi": 0.7,
    "commercial": 0.4, "api-only": 0.4,
    "unknown": 0.0, "proprietary": 0.0,
}

STABILITY_SCORES = {
    "stable": 1.0, "production": 1.0,
    "reliable": 0.7, "recent": 0.7,
    "beta": 0.4, "experimental": 0.4,
    "deprecated": 0.0, "unreliable": 0.0,
}

DOCS_SCORES = {
    "comprehensive": 1.0, "excellent": 1.0,
    "good": 0.7, "basic": 0.7,
    "minimal": 0.4, "poor": 0.4,
    "none": 0.0, "missing": 0.0,
}


# ---------------------------------------------------------------------------
# Score helpers
# ---------------------------------------------------------------------------


def normalize_benchmark_score(benchmark: str, score: float) -> float:
    if score is None:
        return 0.0
    lo, hi = BENCHMARK_RANGES.get(benchmark, (0, 100))
    if hi == lo:
        return 0.0
    return max(0.0, min(1.0, (score - lo) / (hi - lo)))


def compute_benchmark_score(entry: dict[str, Any]) -> float:
    total = 0.0
    weight_used = 0.0
    for name, weight in BENCHMARK_WEIGHTS.items():
        val = entry.get(name)
        if val is not None:
            total += normalize_benchmark_score(name, float(val)) * weight
            weight_used += weight
    if weight_used == 0:
        return 0.0
    return total / weight_used


def compute_cost_efficiency_score(entry: dict[str, Any]) -> float:
    benchmark_score = entry.get("benchmark_score", 0.0) or 0.0
    avg_in = entry.get("price_per_million_input")
    avg_out = entry.get("price_per_million_output")
    context = entry.get("context_length", 0) or 0
    is_free = bool(entry.get("is_free", False))

    if is_free:
        price_eff = 1.0
    elif avg_in is not None and avg_out is not None:
        avg_price = (float(avg_in) + float(avg_out)) / 2
        if avg_price <= 0 or benchmark_score <= 0:
            return 0.0
        max_price, min_price = 100.0, 0.10
        normalized_price = min(
            1.0,
            (avg_price - min_price) / (max_price - min_price),
        )
        price_eff = (1.0 - normalized_price) * 0.5 + benchmark_score * 0.5
    else:
        return 0.0

    if context > 0:
        ctx_bonus = min(0.3, (math.log(context / 4096) / math.log(256)) * 0.3)
        ctx_bonus = max(0.0, ctx_bonus)
    else:
        ctx_bonus = 0.0

    eff = price_eff * 0.7 + ctx_bonus
    return min(1.0, max(0.0, eff))


def compute_accessibility_score(entry: dict[str, Any]) -> float:
    license_type = (entry.get("license_type") or "").lower() or None
    stability = (entry.get("api_stability") or "").lower() or None
    docs = (entry.get("documentation_quality") or "").lower() or None
    license_s = LICENSE_SCORES.get(license_type, 0.7) if license_type else 0.7
    stab_s = STABILITY_SCORES.get(stability, 0.7) if stability else 0.7
    docs_s = DOCS_SCORES.get(docs, 0.7) if docs else 0.7
    return 0.40 * license_s + 0.40 * stab_s + 0.20 * docs_s


def compute_adoption_score(entry: dict[str, Any]) -> float:  # noqa: PLR0911
    """Adoption from OpenRouter programming-category rank or local usage."""

    rank = entry.get("openrouter_programming_rank")
    if rank:
        rank = int(rank)
        if rank <= 5:  # noqa: PLR2004
            return 1.0 - (rank - 1) * 0.04
        if rank <= 10:  # noqa: PLR2004
            return 0.8 - (rank - 6) * 0.04
        if rank <= 20:  # noqa: PLR2004
            return 0.6 - (rank - 11) * 0.02
        if rank <= 50:  # noqa: PLR2004
            return 0.4 - (rank - 21) * 0.00667
        return max(0.0, 0.2 - (rank - 51) * 0.004)

    # Fallback: derive adoption from local generation-job count (apps built).
    apps = int(entry.get("apps", 0) or 0)
    if apps <= 0:
        return 0.0
    return min(1.0, math.log10(apps + 1) / 2.0)


def compute_mss(entry: dict[str, Any]) -> float:
    adoption = entry.get("adoption_score", 0.0) or 0.0
    benchmarks = entry.get("benchmark_score", 0.0) or 0.0
    cost = entry.get("cost_efficiency_score", 0.0) or 0.0
    access = entry.get("accessibility_score", 0.0) or 0.0
    return round(
        0.35 * adoption + 0.30 * benchmarks + 0.20 * cost + 0.15 * access,
        4,
    )


# ---------------------------------------------------------------------------
# Aggregation
# ---------------------------------------------------------------------------


def _local_app_stats() -> dict[str, dict[str, Any]]:
    """Aggregate per-model apps generated and finding rollups."""

    by_model = (
        GenerationJob.objects.exclude(model__isnull=True)
        .values("model__model_id")
        .annotate(
            apps=Count("id"),
            apps_completed=Count("id", filter=Q(status="completed")),
            avg_duration=Avg(
                "duration_seconds",
                filter=Q(status="completed"),
            ),
        )
    )
    out: dict[str, dict[str, Any]] = {}
    for row in by_model:
        out[row["model__model_id"]] = {
            "apps": int(row["apps"]),
            "apps_completed": int(row["apps_completed"]),
            "avg_duration": (
                round(row["avg_duration"], 1) if row["avg_duration"] else 0.0
            ),
            "findings": {"critical": 0, "high": 0, "medium": 0, "low": 0, "info": 0},
        }

    sev_rows = (
        Finding.objects.exclude(
            result__task__generation_job__model__model_id__isnull=True,
        )
        .values(
            "result__task__generation_job__model__model_id",
            "severity",
        )
        .annotate(c=Count("id"))
    )
    for r in sev_rows:
        mid = r["result__task__generation_job__model__model_id"]
        if mid in out:
            out[mid]["findings"][r["severity"]] = int(r["c"])

    return out


def _benchmarks_by_model() -> dict[str, dict[str, float]]:
    out: dict[str, dict[str, float]] = {}
    for r in BenchmarkResult.objects.all().values("model_id", "benchmark", "score"):
        out.setdefault(r["model_id"], {})[r["benchmark"]] = float(r["score"])
    return out


def aggregate_rankings() -> list[dict[str, Any]]:
    """Build the ranking list from LLMModel + benchmarks + local stats."""

    local = _local_app_stats()
    bench = _benchmarks_by_model()

    rows: list[dict[str, Any]] = []
    for m in LLMModel.objects.all():
        local_row = local.get(m.model_id, {})
        bench_row = bench.get(m.model_id, {})

        entry: dict[str, Any] = {
            "model_id": m.model_id,
            "model_name": m.model_name,
            "provider": m.provider,
            "is_free": m.is_free,
            "context_length": m.context_window,
            "price_per_million_input": (
                m.input_price_per_token * 1_000_000
                if m.input_price_per_token
                else None
            ),
            "price_per_million_output": (
                m.output_price_per_token * 1_000_000
                if m.output_price_per_token
                else None
            ),
            "apps": local_row.get("apps", 0),
            "apps_completed": local_row.get("apps_completed", 0),
            "avg_duration": local_row.get("avg_duration", 0.0),
            "findings": local_row.get(
                "findings",
                {"critical": 0, "high": 0, "medium": 0, "low": 0, "info": 0},
            ),
        }
        # Hoist benchmark scores into entry for normalization
        entry.update(bench_row)

        # Pull metadata-driven attributes (license_type, api_stability, etc.)
        meta = m.metadata or {}
        for k in (
            "license_type",
            "api_stability",
            "documentation_quality",
            "openrouter_programming_rank",
        ):
            if k in meta and entry.get(k) is None:
                entry[k] = meta[k]

        # Compute component scores
        entry["benchmark_score"] = round(compute_benchmark_score(entry), 4)
        entry["cost_efficiency_score"] = round(
            compute_cost_efficiency_score(entry), 4,
        )
        entry["accessibility_score"] = round(
            compute_accessibility_score(entry), 4,
        )
        entry["adoption_score"] = round(compute_adoption_score(entry), 4)
        entry["mss_score"] = compute_mss(entry)
        # Backward-compat aliases used by old API consumers.
        entry["composite_score"] = entry["mss_score"]

        rows.append(entry)

    rows.sort(key=lambda r: r.get("mss_score") or 0.0, reverse=True)
    return rows


# ---------------------------------------------------------------------------
# Filtering & top-N
# ---------------------------------------------------------------------------


def filter_rankings(  # noqa: PLR0913, C901, PLR0912
    rankings: list[dict[str, Any]],
    *,
    max_price: float | None = None,
    min_context: int | None = None,
    providers: list[str] | None = None,
    include_free: bool = True,
    min_composite: float | None = None,
    has_benchmarks: bool = False,
    search: str = "",
) -> list[dict[str, Any]]:
    out = []
    needle = (search or "").strip().lower()
    provs = [p.lower() for p in (providers or [])]
    for entry in rankings:
        if max_price is not None:
            price = entry.get("price_per_million_input") or 0
            if price > max_price and not entry.get("is_free"):
                continue
        if not include_free and entry.get("is_free"):
            continue
        if min_context is not None:
            c = entry.get("context_length")
            if not c or c < min_context:
                continue
        if provs:
            if (entry.get("provider") or "").lower() not in provs:
                continue
        if min_composite is not None:
            mss = entry.get("mss_score")
            if mss is None or mss < min_composite:
                continue
        if has_benchmarks and not (entry.get("benchmark_score") or 0) > 0:
            continue
        if needle:
            haystack = " ".join(
                [
                    entry.get("model_name") or "",
                    entry.get("model_id") or "",
                    entry.get("provider") or "",
                ],
            ).lower()
            if needle not in haystack:
                continue
        out.append(entry)
    return out


SORT_KEY_MAP = {
    "mss": "mss_score",
    "composite": "mss_score",
    "adoption": "adoption_score",
    "benchmark": "benchmark_score",
    "cost": "cost_efficiency_score",
    "access": "accessibility_score",
    "context": "context_length",
    "price": "price_per_million_input",
    "name": "model_name",
    "apps": "apps",
}


def sort_rankings(
    rankings: list[dict[str, Any]],
    *,
    sort_by: str = "mss",
    sort_dir: str = "desc",
) -> list[dict[str, Any]]:
    key = SORT_KEY_MAP.get(sort_by, sort_by) or "mss_score"
    reverse = sort_dir == "desc"

    def get_val(item: dict[str, Any]) -> Any:
        v = item.get(key)
        if v is None:
            return float("-inf") if reverse else float("inf")
        return v

    return sorted(rankings, key=get_val, reverse=reverse)


def get_top_models(
    count: int = 10,
    weights: dict[str, float] | None = None,
    **filter_kwargs: Any,
) -> list[dict[str, Any]]:
    rankings = filter_rankings(aggregate_rankings(), **filter_kwargs)
    if weights:
        for entry in rankings:
            total, total_weight = 0.0, 0.0
            for k, w in weights.items():
                v = entry.get(k)
                if v is not None:
                    total += float(v) * w
                    total_weight += w
            entry["composite_score"] = (
                round(total / total_weight, 4) if total_weight else None
            )
        rankings.sort(
            key=lambda x: x.get("composite_score") or 0.0,
            reverse=True,
        )
    else:
        rankings = sort_rankings(rankings, sort_by="mss", sort_dir="desc")
    return rankings[: max(1, min(count, 100))]


def get_status() -> dict[str, Any]:
    """Diagnostic info: counts of seeded benchmarks per benchmark name."""

    counts: dict[str, int] = {}
    for r in (
        BenchmarkResult.objects.values("benchmark").annotate(c=Count("id"))
    ):
        counts[r["benchmark"]] = int(r["c"])
    return {
        "benchmarks": counts,
        "total_benchmark_rows": sum(counts.values()),
        "models_with_benchmarks": (
            BenchmarkResult.objects.values("model_id").distinct().count()
        ),
        "total_models": LLMModel.objects.count(),
    }

"""Django Ninja API views for LLM models."""

from __future__ import annotations

from django.db.models import Avg
from django.db.models import Q
from django.shortcuts import get_object_or_404
from ninja import Query
from ninja import Router

from llm_lab.common.pagination import paginate_queryset
from llm_lab.llm_models.api.schema import LLMModelListSchema
from llm_lab.llm_models.api.schema import LLMModelSchema
from llm_lab.llm_models.api.schema import PaginatedModelsSchema
from llm_lab.llm_models.api.schema import StatsSchema
from llm_lab.llm_models.api.schema import SyncResultSchema
from llm_lab.llm_models.models import LLMModel
from llm_lab.llm_models.services import sync_models_from_openrouter

router = Router(tags=["models"])

SORT_FIELD_MAP = {
    "model_name": "model_name",
    "provider": "provider",
    "context_window": "context_window",
    "input_price": "input_price_per_token",
    "output_price": "output_price_per_token",
    "cost_efficiency": "cost_efficiency",
    "created_at": "created_at",
    "max_output": "max_output_tokens",
}

PRICE_PER_MILLION_THRESHOLDS = {
    "free": (None, None, True),  # is_free=True
    "low": (0, 1e-6, False),  # <$1/1M → <$0.000001/token
    "medium": (1e-6, 10e-6, False),  # $1-$10/1M
    "high": (10e-6, None, False),  # >$10/1M
}

CONTEXT_RANGE_THRESHOLDS = {
    "small": (0, 8_000),
    "medium": (8_000, 32_000),
    "large": (32_000, 128_000),
    "xlarge": (128_000, None),
}


def _apply_search(qs, search: str):
    if search:
        qs = qs.filter(
            Q(model_name__icontains=search)
            | Q(provider__icontains=search)
            | Q(model_id__icontains=search)
            | Q(description__icontains=search),
        )
    return qs


def _apply_capability_filter(qs, capability: str):
    cap_map = {
        "vision": "supports_vision",
        "function_calling": "supports_function_calling",
        "streaming": "supports_streaming",
        "json_mode": "supports_json_mode",
    }
    field = cap_map.get(capability)
    if field:
        qs = qs.filter(**{field: True})
    return qs


def _apply_price_range(qs, price_range: str):
    if price_range not in PRICE_PER_MILLION_THRESHOLDS:
        return qs
    low, high, is_free = PRICE_PER_MILLION_THRESHOLDS[price_range]
    if is_free:
        return qs.filter(is_free=True)
    if low is not None:
        qs = qs.filter(input_price_per_token__gte=low)
    if high is not None:
        qs = qs.filter(input_price_per_token__lt=high)
    return qs


def _apply_context_range(qs, context_range: str):
    if context_range not in CONTEXT_RANGE_THRESHOLDS:
        return qs
    low, high = CONTEXT_RANGE_THRESHOLDS[context_range]
    if low is not None:
        qs = qs.filter(context_window__gte=low)
    if high is not None:
        qs = qs.filter(context_window__lt=high)
    return qs


def _apply_sorting(qs, sort_by: str, sort_dir: str):
    if sort_by and sort_by in SORT_FIELD_MAP:
        order_field = SORT_FIELD_MAP[sort_by]
        if sort_dir == "desc":
            order_field = f"-{order_field}"
        return qs.order_by(order_field, "model_name")
    return qs.order_by("provider", "model_name")


@router.get("/", response=PaginatedModelsSchema)
def list_models(  # noqa: PLR0913
    request,
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=200),
    search: str = Query(""),
    provider: str = Query(""),
    capability: str = Query(""),
    free_only: bool = Query(False),  # noqa: FBT001, FBT003
    sort_by: str = Query(""),
    sort_dir: str = Query("asc"),
    price_range: str = Query(""),
    context_range: str = Query(""),
):
    """List models with filtering, search, sorting, and pagination."""
    qs = LLMModel.objects.all()
    qs = _apply_search(qs, search)

    if provider:
        qs = qs.filter(provider__iexact=provider)
    if free_only:
        qs = qs.filter(is_free=True)
    if capability:
        qs = _apply_capability_filter(qs, capability)
    if price_range:
        qs = _apply_price_range(qs, price_range)
    if context_range:
        qs = _apply_context_range(qs, context_range)

    qs = _apply_sorting(qs, sort_by, sort_dir)

    page_qs, total, page, pages = paginate_queryset(qs, page, per_page)

    items = [LLMModelListSchema.from_model(m) for m in page_qs]
    return PaginatedModelsSchema(
        items=items,
        total=total,
        page=page,
        per_page=per_page,
        pages=pages,
    )


@router.get("/stats/", response=StatsSchema)
def get_stats(request):
    """Get aggregate statistics about loaded models."""
    qs = LLMModel.objects.all()
    # Exclude models with negative sentinel prices (e.g. -1) from averages
    paid_qs = qs.filter(input_price_per_token__gte=0)
    agg = paid_qs.aggregate(
        avg_in=Avg("input_price_per_token"),
        avg_out=Avg("output_price_per_token"),
    )
    return StatsSchema(
        total=qs.count(),
        providers=qs.values("provider").distinct().count(),
        free=qs.filter(is_free=True).count(),
        avg_input_price=round((agg["avg_in"] or 0) * 1_000_000, 4),
        avg_output_price=round((agg["avg_out"] or 0) * 1_000_000, 4),
    )


@router.get("/providers/", response=list[str])
def list_providers(request):
    """Return distinct provider names."""
    return list(
        LLMModel.objects.values_list("provider", flat=True)
        .distinct()
        .order_by("provider"),
    )


@router.post("/sync/", response=SyncResultSchema)
def sync_models(request):
    """Fetch models from OpenRouter and upsert into DB."""
    return sync_models_from_openrouter()


# Slug-based routes MUST come after all fixed-path routes
@router.get("/detail/{slug}/", response=LLMModelSchema)
def get_model(request, slug: str):
    """Get a single model by its canonical slug."""
    return get_object_or_404(LLMModel, canonical_slug=slug)


@router.delete("/detail/{slug}/")
def delete_model(request, slug: str):
    """Delete a model by slug."""
    model = get_object_or_404(LLMModel, canonical_slug=slug)
    model.delete()
    return {"success": True}


@router.get("/detail/{slug}/related/", response=list[LLMModelListSchema])
def get_related_models(request, slug: str, limit: int = Query(10, ge=1, le=20)):
    """Get models from the same provider, excluding the current model."""
    model = get_object_or_404(LLMModel, canonical_slug=slug)
    related = (
        LLMModel.objects.filter(provider=model.provider)
        .exclude(pk=model.pk)
        .order_by("-cost_efficiency", "model_name")[:limit]
    )
    return [LLMModelListSchema.from_model(m) for m in related]

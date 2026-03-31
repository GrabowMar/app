"""Django Ninja API views for LLM models."""

from django.db.models import Avg
from django.db.models import Q
from django.shortcuts import get_object_or_404
from ninja import Query
from ninja import Router

from llm_lab.llm_models.api.schema import LLMModelListSchema
from llm_lab.llm_models.api.schema import LLMModelSchema
from llm_lab.llm_models.api.schema import PaginatedModelsSchema
from llm_lab.llm_models.api.schema import StatsSchema
from llm_lab.llm_models.api.schema import SyncResultSchema
from llm_lab.llm_models.models import LLMModel
from llm_lab.llm_models.services import sync_models_from_openrouter

router = Router(tags=["models"])


@router.get("/", response=PaginatedModelsSchema)
def list_models(  # noqa: PLR0913
    request,
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=200),
    search: str = Query(""),
    provider: str = Query(""),
    capability: str = Query(""),
    free_only: bool = Query(False),  # noqa: FBT001, FBT003
):
    """List models with filtering, search, and pagination."""
    qs = LLMModel.objects.all()

    if search:
        qs = qs.filter(
            Q(model_name__icontains=search)
            | Q(provider__icontains=search)
            | Q(model_id__icontains=search)
            | Q(description__icontains=search),
        )

    if provider:
        qs = qs.filter(provider__iexact=provider)

    if free_only:
        qs = qs.filter(is_free=True)

    if capability:
        cap_map = {
            "vision": "supports_vision",
            "function_calling": "supports_function_calling",
            "streaming": "supports_streaming",
            "json_mode": "supports_json_mode",
        }
        field = cap_map.get(capability)
        if field:
            qs = qs.filter(**{field: True})

    qs = qs.order_by("provider", "model_name")
    total = qs.count()
    pages = max(1, (total + per_page - 1) // per_page)
    page = min(page, pages)
    offset = (page - 1) * per_page

    items = [LLMModelListSchema.from_model(m) for m in qs[offset : offset + per_page]]
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
    agg = qs.aggregate(
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

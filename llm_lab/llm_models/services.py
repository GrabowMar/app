"""OpenRouter integration — fetch models and upsert into the database."""

import logging
import time
from typing import Any

import requests
from django.conf import settings
from django.db import IntegrityError

from llm_lab.llm_models.models import LLMModel

logger = logging.getLogger(__name__)


def normalize_model_identifier(value: str) -> str:
    """Normalize a model identifier into the canonical slug format."""
    return value.strip().lower().replace("/", "_").replace(":", "_").replace(" ", "_")


def _build_canonical_slug(model_id: str, raw_slug: str = "") -> str:
    candidate = raw_slug.strip() or model_id
    return normalize_model_identifier(candidate)


def _coerce_bool(value: Any, default: bool = False) -> bool:
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    return str(value).strip().lower() in {"1", "true", "yes", "on"}


def _coerce_float(value: Any, default: float = 0.0) -> float:
    try:
        if value in (None, ""):
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def _coerce_int(value: Any, default: int = 0) -> int:
    try:
        if value in (None, ""):
            return default
        return int(value)
    except (TypeError, ValueError):
        return default


def _update_or_create_model(
    model_id: str,
    canonical_slug: str,
    defaults: dict[str, Any],
) -> bool:
    try:
        LLMModel.objects.update_or_create(
            model_id=model_id,
            defaults={**defaults, "canonical_slug": canonical_slug},
        )
        return True
    except IntegrityError:
        try:
            LLMModel.objects.update_or_create(
                canonical_slug=canonical_slug,
                defaults={**defaults, "model_id": model_id},
            )
            return True
        except IntegrityError:
            logger.exception("Failed to upsert model %s", model_id)
            return False


def fetch_openrouter_models() -> list[dict]:
    """Fetch all models from the OpenRouter API. Returns raw model dicts."""
    api_key = settings.OPENROUTER_API_KEY
    if not api_key:
        logger.error("OPENROUTER_API_KEY not configured")
        return []

    headers = {
        "Authorization": f"Bearer {api_key}",
        "HTTP-Referer": "https://llm-lab.local",
        "X-Title": "LLM Eval Lab",
        "Content-Type": "application/json",
    }

    logger.info("Fetching models from OpenRouter API…")
    start = time.time()

    try:
        resp = requests.get(
            settings.OPENROUTER_API_URL,
            headers=headers,
            timeout=30,
        )
        resp.raise_for_status()
    except requests.RequestException:
        logger.exception("OpenRouter API request failed")
        return []

    data = resp.json()
    models = data.get("data", [])
    duration = time.time() - start
    logger.info("Fetched %d models from OpenRouter in %.2fs", len(models), duration)
    return models


def upsert_openrouter_models(models_payload: list[dict]) -> int:  # noqa: C901, PLR0912, PLR0915
    """Upsert a list of OpenRouter model payloads into LLMModel.

    Returns count upserted.
    """
    upserted = 0
    for model_data in models_payload:
        model_id = model_data.get("id")
        if not model_id:
            continue

        # Build canonical slug
        canonical = model_id.replace("/", "_").replace(":", "_")
        raw_cs = model_data.get("canonical_slug", "")
        if raw_cs:
            canonical = raw_cs
        canonical = _build_canonical_slug(model_id, canonical)

        provider = model_id.split("/")[0] if "/" in model_id else "unknown"
        model_name = model_data.get("name") or model_id.split("/")[-1]
        description = model_data.get("description", "") or ""

        # Pricing
        pricing = model_data.get("pricing") or {}
        try:
            prompt_price = float(
                pricing.get("prompt") or pricing.get("prompt_tokens") or 0,
            )
        except (TypeError, ValueError):
            prompt_price = 0.0
        try:
            completion_price = float(
                pricing.get("completion") or pricing.get("completion_tokens") or 0,
            )
        except (TypeError, ValueError):
            completion_price = 0.0

        # Context window
        top_provider = model_data.get("top_provider") or {}
        context_window = 0
        context_sources = [
            top_provider.get("context_length"),
            model_data.get("context_length"),
        ]
        for src in context_sources:
            if src:
                try:
                    context_window = int(src)
                    break
                except (TypeError, ValueError):
                    pass

        # Max output tokens
        max_output = 0
        for src in [
            top_provider.get("max_completion_tokens"),
            model_data.get("max_output_tokens"),
        ]:
            if src:
                try:
                    max_output = int(src)
                    break
                except (TypeError, ValueError):
                    pass

        # Capability booleans
        arch = model_data.get("architecture") or {}
        modality = (arch.get("modality") or "").lower()
        supported_params = model_data.get("supported_parameters") or []

        supports_vision = bool(
            model_data.get("supports_vision") or "image" in modality,
        )
        supports_function_calling = bool(
            model_data.get("supports_tool_calling")
            or model_data.get("supports_function_calling")
            or any(p in ["tools", "tool_choice"] for p in supported_params),
        )
        supports_json_mode = bool(
            model_data.get("supports_json")
            or model_data.get("supports_json_mode")
            or "response_format" in supported_params,
        )
        supports_streaming = bool(
            model_data.get("supports_streaming") or "stream" in supported_params,
        )
        is_free = bool(
            model_data.get(
                "is_free",
                prompt_price == 0 and completion_price == 0,
            ),
        )

        cost_eff = LLMModel.calculate_cost_efficiency(
            context_window,
            prompt_price,
            completion_price,
        )

        # Build metadata
        meta: dict = {}
        meta["openrouter_model_id"] = model_data.get("id")
        meta["openrouter_name"] = model_data.get("name")
        meta["openrouter_created"] = model_data.get("created")
        meta["openrouter_description"] = model_data.get("description")
        meta["openrouter_pricing"] = model_data.get("pricing")
        meta["openrouter_top_provider"] = model_data.get("top_provider")
        meta["openrouter_supported_parameters"] = model_data.get("supported_parameters")
        if arch:
            meta["architecture_modality"] = arch.get("modality")
            meta["architecture_tokenizer"] = arch.get("tokenizer")
            meta["architecture_instruct_type"] = arch.get("instruct_type")
            meta["architecture_input_modalities"] = arch.get("input_modalities")
            meta["architecture_output_modalities"] = arch.get("output_modalities")

        defaults = {
            "provider": provider,
            "model_name": model_name,
            "description": description[:5000],
            "is_free": is_free,
            "context_window": context_window,
            "max_output_tokens": max_output,
            "input_price_per_token": prompt_price,
            "output_price_per_token": completion_price,
            "supports_function_calling": supports_function_calling,
            "supports_vision": supports_vision,
            "supports_streaming": supports_streaming,
            "supports_json_mode": supports_json_mode,
            "cost_efficiency": cost_eff,
            "capabilities_json": model_data,
            "metadata": meta,
        }

        if _update_or_create_model(model_id, canonical, defaults):
            upserted += 1

    return upserted


def extract_import_models(payload: Any) -> list[dict[str, Any]]:
    """Extract a normalized list of model payloads from import JSON."""
    if isinstance(payload, list):
        return [item for item in payload if isinstance(item, dict)]

    if isinstance(payload, dict):
        if isinstance(payload.get("models"), list):
            return [item for item in payload["models"] if isinstance(item, dict)]
        if isinstance(payload.get("data"), list):
            return [item for item in payload["data"] if isinstance(item, dict)]
        return [payload]

    return []


def upsert_imported_models(models_payload: list[dict[str, Any]]) -> int:
    """Upsert models from an exported/internal JSON representation."""
    upserted = 0

    for model_data in models_payload:
        model_id = str(model_data.get("model_id") or model_data.get("id") or "").strip()
        if not model_id:
            continue

        canonical_slug = _build_canonical_slug(
            model_id,
            str(model_data.get("canonical_slug") or ""),
        )
        provider = str(
            model_data.get("provider")
            or (model_id.split("/", 1)[0] if "/" in model_id else "unknown"),
        ).strip()
        model_name = str(
            model_data.get("model_name")
            or model_data.get("name")
            or model_id.split("/", 1)[-1],
        ).strip()
        description = str(model_data.get("description") or "")

        input_price = _coerce_float(model_data.get("input_price_per_token"))
        output_price = _coerce_float(model_data.get("output_price_per_token"))
        if input_price == 0 and model_data.get("input_price_per_million") not in (None, ""):
            input_price = _coerce_float(model_data.get("input_price_per_million")) / 1_000_000
        if output_price == 0 and model_data.get("output_price_per_million") not in (None, ""):
            output_price = _coerce_float(model_data.get("output_price_per_million")) / 1_000_000

        context_window = _coerce_int(model_data.get("context_window"))
        max_output_tokens = _coerce_int(model_data.get("max_output_tokens"))

        capabilities_json = model_data.get("capabilities_json")
        if not isinstance(capabilities_json, dict):
            capabilities_json = {}
            for field in (
                "capabilities",
                "supported_parameters",
                "top_provider",
                "pricing",
                "architecture",
            ):
                if field in model_data:
                    capabilities_json[field] = model_data[field]

        metadata = model_data.get("metadata")
        if not isinstance(metadata, dict):
            metadata = {}

        capabilities = model_data.get("capabilities")
        supports_function_calling = _coerce_bool(
            model_data.get("supports_function_calling"),
            isinstance(capabilities, list) and "Function Calling" in capabilities,
        )
        supports_vision = _coerce_bool(
            model_data.get("supports_vision"),
            isinstance(capabilities, list) and "Vision" in capabilities,
        )
        supports_streaming = _coerce_bool(
            model_data.get("supports_streaming"),
            isinstance(capabilities, list) and "Streaming" in capabilities,
        )
        supports_json_mode = _coerce_bool(
            model_data.get("supports_json_mode"),
            isinstance(capabilities, list) and "JSON Mode" in capabilities,
        )
        is_free = _coerce_bool(
            model_data.get("is_free"),
            input_price == 0 and output_price == 0,
        )

        cost_efficiency = _coerce_float(model_data.get("cost_efficiency"))
        if cost_efficiency <= 0:
            cost_efficiency = LLMModel.calculate_cost_efficiency(
                context_window,
                input_price,
                output_price,
            )

        defaults = {
            "provider": provider,
            "model_name": model_name,
            "description": description[:5000],
            "is_free": is_free,
            "context_window": context_window,
            "max_output_tokens": max_output_tokens,
            "input_price_per_token": input_price,
            "output_price_per_token": output_price,
            "supports_function_calling": supports_function_calling,
            "supports_vision": supports_vision,
            "supports_streaming": supports_streaming,
            "supports_json_mode": supports_json_mode,
            "cost_efficiency": cost_efficiency,
            "capabilities_json": capabilities_json,
            "metadata": metadata,
        }

        if _update_or_create_model(model_id, canonical_slug, defaults):
            upserted += 1

    return upserted


def import_models_from_payload(payload: Any) -> dict[str, int]:
    """Import models from OpenRouter payloads or exported model JSON."""
    items = extract_import_models(payload)
    openrouter_items: list[dict[str, Any]] = []
    exported_items: list[dict[str, Any]] = []

    for item in items:
        if "model_id" in item or "canonical_slug" in item:
            exported_items.append(item)
            continue
        if "id" in item:
            openrouter_items.append(item)

    imported = 0
    if openrouter_items:
        imported += upsert_openrouter_models(openrouter_items)
    if exported_items:
        imported += upsert_imported_models(exported_items)

    return {"count": len(items), "imported": imported}


def refresh_model_from_openrouter(model: LLMModel) -> bool:
    """Refresh a single model from the OpenRouter catalog."""
    models_payload = fetch_openrouter_models()
    if not models_payload:
        return False

    candidates = {
        model.model_id.strip().lower(),
        model.canonical_slug.strip().lower(),
        normalize_model_identifier(model.model_id),
        normalize_model_identifier(model.canonical_slug),
    }

    for model_data in models_payload:
        model_id = str(model_data.get("id") or "").strip()
        if not model_id:
            continue

        canonical_slug = _build_canonical_slug(
            model_id,
            str(model_data.get("canonical_slug") or ""),
        )
        if model_id.lower() in candidates or canonical_slug in candidates:
            return upsert_openrouter_models([model_data]) == 1

    return False


def sync_models_from_openrouter() -> dict:
    """Full sync: fetch from OpenRouter and upsert into DB."""
    models_payload = fetch_openrouter_models()
    if not models_payload:
        return {"fetched": 0, "upserted": 0}
    upserted = upsert_openrouter_models(models_payload)
    return {"fetched": len(models_payload), "upserted": upserted}

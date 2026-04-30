"""Automation business logic services."""

from __future__ import annotations

import copy
from datetime import UTC
from datetime import datetime
from typing import TYPE_CHECKING
from typing import Any

if TYPE_CHECKING:
    from llm_lab.automation.models import Pipeline
    from llm_lab.automation.models import PipelineRun
    from llm_lab.users.models import User

_REQUIRED_STEP_FIELDS: dict[str, list[str]] = {
    "generate": ["model_id", "template_slug"],
    "analyze": ["job_ids"],
    "report": ["report_type"],
    "wait": ["seconds"],
    "notify": ["channel"],
    "script": ["code"],
}


def validate_pipeline_dsl(config: dict[str, Any]) -> list[str]:
    """Validate a pipeline DSL config. Returns a list of error strings."""
    errors: list[str] = []
    steps = config.get("steps", [])
    if not isinstance(steps, list):
        errors.append("'steps' must be a list")
        return errors
    step_ids: set[str] = set()
    for i, step in enumerate(steps):
        prefix = f"Step {i}"
        if not isinstance(step, dict):
            errors.append(f"{prefix}: must be an object")
            continue
        if not step.get("name"):
            errors.append(f"{prefix}: 'name' is required")
        kind = step.get("kind")
        if not kind:
            errors.append(f"{prefix}: 'kind' is required")
        else:
            required = _REQUIRED_STEP_FIELDS.get(kind, [])
            step_config = step.get("config", {})
            for field in required:
                if not step_config.get(field):
                    errors.append(f"{prefix} (kind={kind}): config.{field} is required")
        step_id = step.get("id")
        if step_id:
            if step_id in step_ids:
                errors.append(f"{prefix}: duplicate step id '{step_id}'")
            step_ids.add(step_id)
    for i, step in enumerate(steps):
        if not isinstance(step, dict):
            continue
        for dep in step.get("depends_on", []):
            if dep not in step_ids:
                errors.append(
                    f"Step {i}: depends_on references unknown step id '{dep}'",
                )
    return errors


def clone_pipeline(pipeline: Pipeline, new_name: str) -> Pipeline:
    """Deep-copy a pipeline and all its steps under a new name."""
    from llm_lab.automation.models import Pipeline as PipelineModel
    from llm_lab.automation.models import PipelineStep

    new_pipeline = PipelineModel.objects.create(
        owner=pipeline.owner,
        name=new_name,
        description=pipeline.description,
        version=1,
        status=PipelineModel.Status.DRAFT,
        config=copy.deepcopy(pipeline.config),
        tags=copy.deepcopy(pipeline.tags),
    )
    for step in pipeline.steps.order_by("order"):
        PipelineStep.objects.create(
            pipeline=new_pipeline,
            order=step.order,
            name=step.name,
            kind=step.kind,
            config=copy.deepcopy(step.config),
            depends_on=copy.deepcopy(step.depends_on),
        )
    return new_pipeline


def next_cron_time(expr: str, after: datetime | None = None) -> datetime:
    """Return the next scheduled datetime for a cron expression."""
    from croniter import croniter

    base = after if after is not None else datetime.now(UTC)
    return croniter(expr, base).get_next(datetime)


def trigger_run(pipeline: Pipeline, params: dict[str, Any], user: User) -> PipelineRun:
    """Create a pending PipelineRun. Execution engine added in Phase 7b."""
    from llm_lab.automation.models import PipelineRun
    from llm_lab.automation.models import PipelineStep
    from llm_lab.automation.models import PipelineStepRun

    run = PipelineRun.objects.create(
        pipeline=pipeline,
        triggered_by=user,
        status="pending",
        params=params,
    )
    for step in PipelineStep.objects.filter(pipeline=pipeline).order_by("order"):
        PipelineStepRun.objects.create(
            run=run,
            step=step,
            status="pending",
        )
    return run

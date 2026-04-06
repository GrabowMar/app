"""Django Ninja API views for generation."""

from __future__ import annotations

from django.shortcuts import get_object_or_404
from ninja import Query
from ninja import Router

from llm_lab.common.pagination import paginate_queryset
from llm_lab.generation.api.schema import AppRequirementCreateSchema
from llm_lab.generation.api.schema import AppRequirementTemplateSchema
from llm_lab.generation.api.schema import BatchCreateResponseSchema
from llm_lab.generation.api.schema import CopilotIterationSchema
from llm_lab.generation.api.schema import CopilotJobCreateSchema
from llm_lab.generation.api.schema import CustomJobCreateSchema
from llm_lab.generation.api.schema import GenerationArtifactSchema
from llm_lab.generation.api.schema import GenerationBatchSchema
from llm_lab.generation.api.schema import GenerationJobListSchema
from llm_lab.generation.api.schema import GenerationJobSchema
from llm_lab.generation.api.schema import PaginatedJobsSchema
from llm_lab.generation.api.schema import PromptTemplateCreateSchema
from llm_lab.generation.api.schema import PromptTemplateSchema
from llm_lab.generation.api.schema import ScaffoldingJobCreateSchema
from llm_lab.generation.api.schema import ScaffoldingTemplateCreateSchema
from llm_lab.generation.api.schema import ScaffoldingTemplateSchema
from llm_lab.generation.models import AppRequirementTemplate
from llm_lab.generation.models import GenerationBatch
from llm_lab.generation.models import GenerationJob
from llm_lab.generation.models import PromptTemplate
from llm_lab.generation.models import ScaffoldingTemplate
from llm_lab.llm_models.models import LLMModel

router = Router(tags=["generation"])


def _dispatch_job(job: GenerationJob) -> None:
    """Run a generation job — sync in-process (Celery worker not required)."""
    import threading  # noqa: PLC0415

    from llm_lab.generation.services.generation_service import GenerationService

    def _run() -> None:
        service = GenerationService()
        service.execute(
            GenerationJob.objects.select_related(
                "model",
                "app_requirement",
                "scaffolding_template",
                "backend_prompt_template",
                "frontend_prompt_template",
                "batch",
            ).get(id=job.id),
        )

    thread = threading.Thread(target=_run, daemon=True)
    thread.start()


# -- Scaffolding Templates ---------------------------------------------


@router.get("/scaffolding-templates/", response=list[ScaffoldingTemplateSchema])
def list_scaffolding_templates(request):
    """List all scaffolding templates."""
    return ScaffoldingTemplate.objects.all()


@router.post("/scaffolding-templates/", response=ScaffoldingTemplateSchema)
def create_scaffolding_template(request, payload: ScaffoldingTemplateCreateSchema):
    """Create a new scaffolding template."""
    return ScaffoldingTemplate.objects.create(
        **payload.dict(),
        created_by=request.auth,
    )


@router.get("/scaffolding-templates/{slug}/", response=ScaffoldingTemplateSchema)
def get_scaffolding_template(request, slug: str):
    return get_object_or_404(ScaffoldingTemplate, slug=slug)


@router.put("/scaffolding-templates/{slug}/", response=ScaffoldingTemplateSchema)
def update_scaffolding_template(
    request,
    slug: str,
    payload: ScaffoldingTemplateCreateSchema,
):
    template = get_object_or_404(ScaffoldingTemplate, slug=slug)
    for attr, value in payload.dict().items():
        setattr(template, attr, value)
    template.save()
    return template


@router.delete("/scaffolding-templates/{slug}/")
def delete_scaffolding_template(request, slug: str):
    template = get_object_or_404(ScaffoldingTemplate, slug=slug)
    template.delete()
    return {"success": True}


# -- App Requirement Templates ------------------------------------------


@router.get("/app-templates/", response=list[AppRequirementTemplateSchema])
def list_app_templates(request):
    """List all app requirement templates."""
    return AppRequirementTemplate.objects.all()


@router.post("/app-templates/", response=AppRequirementTemplateSchema)
def create_app_template(request, payload: AppRequirementCreateSchema):
    return AppRequirementTemplate.objects.create(
        **payload.dict(),
        created_by=request.auth,
    )


@router.get("/app-templates/{slug}/", response=AppRequirementTemplateSchema)
def get_app_template(request, slug: str):
    return get_object_or_404(AppRequirementTemplate, slug=slug)


@router.put("/app-templates/{slug}/", response=AppRequirementTemplateSchema)
def update_app_template(request, slug: str, payload: AppRequirementCreateSchema):
    template = get_object_or_404(AppRequirementTemplate, slug=slug)
    for attr, value in payload.dict().items():
        setattr(template, attr, value)
    template.save()
    return template


@router.delete("/app-templates/{slug}/")
def delete_app_template(request, slug: str):
    template = get_object_or_404(AppRequirementTemplate, slug=slug)
    template.delete()
    return {"success": True}


# -- Prompt Templates ---------------------------------------------------


@router.get("/prompt-templates/", response=list[PromptTemplateSchema])
def list_prompt_templates(request, stage: str = Query(""), role: str = Query("")):
    """List prompt templates with optional filtering."""
    qs = PromptTemplate.objects.all()
    if stage:
        qs = qs.filter(stage=stage)
    if role:
        qs = qs.filter(role=role)
    return qs


@router.post("/prompt-templates/", response=PromptTemplateSchema)
def create_prompt_template(request, payload: PromptTemplateCreateSchema):
    return PromptTemplate.objects.create(**payload.dict(), created_by=request.auth)


@router.get("/prompt-templates/{slug}/", response=PromptTemplateSchema)
def get_prompt_template(request, slug: str):
    return get_object_or_404(PromptTemplate, slug=slug)


@router.put("/prompt-templates/{slug}/", response=PromptTemplateSchema)
def update_prompt_template(request, slug: str, payload: PromptTemplateCreateSchema):
    template = get_object_or_404(PromptTemplate, slug=slug)
    for attr, value in payload.dict().items():
        setattr(template, attr, value)
    template.save()
    return template


@router.delete("/prompt-templates/{slug}/")
def delete_prompt_template(request, slug: str):
    template = get_object_or_404(PromptTemplate, slug=slug)
    template.delete()
    return {"success": True}


# -- Generation Jobs ----------------------------------------------------

# NOTE: Job creation endpoints MUST be defined before {job_id} routes
# otherwise Django Ninja matches "custom", "scaffolding", "copilot" as job_id.


@router.post("/jobs/custom/", response=GenerationJobSchema)
def create_custom_job(request, payload: CustomJobCreateSchema):
    """Create a custom mode generation job."""
    model = get_object_or_404(LLMModel, id=payload.model_id)
    job = GenerationJob.objects.create(
        mode=GenerationJob.Mode.CUSTOM,
        created_by=request.auth,
        model=model,
        custom_system_prompt=payload.system_prompt,
        custom_user_prompt=payload.user_prompt,
        temperature=payload.temperature,
        max_tokens=payload.max_tokens,
    )
    _dispatch_job(job)
    return GenerationJob.objects.get(id=job.id)


@router.post("/jobs/scaffolding/", response=BatchCreateResponseSchema)
def create_scaffolding_jobs(request, payload: ScaffoldingJobCreateSchema):
    """Create scaffolding mode jobs (templates x models)."""
    scaffolding = get_object_or_404(
        ScaffoldingTemplate,
        id=payload.scaffolding_template_id,
    )
    app_reqs = AppRequirementTemplate.objects.filter(
        id__in=payload.app_requirement_ids,
    )
    models_qs = LLMModel.objects.filter(id__in=payload.model_ids)

    batch = GenerationBatch.objects.create(
        name=f"Scaffolding batch - {scaffolding.name}",
        mode="scaffolding",
        total_jobs=app_reqs.count() * models_qs.count(),
        created_by=request.auth,
    )

    job_count = 0
    for app_req in app_reqs:
        for model in models_qs:
            job = GenerationJob.objects.create(
                mode=GenerationJob.Mode.SCAFFOLDING,
                created_by=request.auth,
                batch=batch,
                model=model,
                scaffolding_template=scaffolding,
                app_requirement=app_req,
                temperature=payload.temperature,
                max_tokens=payload.max_tokens,
            )
            job_count += 1

    # Dispatch all jobs in background threads
    for pending_job in batch.jobs.all():
        _dispatch_job(pending_job)

    return BatchCreateResponseSchema(
        batch_id=batch.id,
        job_count=job_count,
        status="pending",
    )


@router.post("/jobs/copilot/", response=GenerationJobSchema)
def create_copilot_job(request, payload: CopilotJobCreateSchema):
    """Create a copilot mode generation job."""
    model = None
    if payload.model_id:
        model = get_object_or_404(LLMModel, id=payload.model_id)
    scaffolding = None
    if payload.scaffolding_template_id:
        scaffolding = get_object_or_404(
            ScaffoldingTemplate,
            id=payload.scaffolding_template_id,
        )

    job = GenerationJob.objects.create(
        mode=GenerationJob.Mode.COPILOT,
        created_by=request.auth,
        model=model,
        scaffolding_template=scaffolding,
        copilot_description=payload.description,
        copilot_max_iterations=payload.max_iterations,
        copilot_use_open_source=payload.use_open_source,
    )
    _dispatch_job(job)
    return GenerationJob.objects.get(id=job.id)


@router.get("/jobs/", response=PaginatedJobsSchema)
def list_jobs(
    request,
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    mode: str = Query(""),
    status: str = Query(""),
):
    """List generation jobs with pagination and filters."""
    qs = (
        GenerationJob.objects.filter(created_by=request.auth)
        .select_related(
            "model",
            "app_requirement",
            "scaffolding_template",
        )
        .order_by("-created_at")
    )
    if mode:
        qs = qs.filter(mode=mode)
    if status:
        qs = qs.filter(status=status)

    page_qs, total, page, pages = paginate_queryset(qs, page, per_page)

    items = [
        GenerationJobListSchema(
            id=job.id,
            mode=job.mode,
            status=job.status,
            model_name=job.model.model_name if job.model else None,
            model_id_str=job.model.model_id if job.model else None,
            template_name=(job.app_requirement.name if job.app_requirement else None),
            scaffolding_name=(
                job.scaffolding_template.name if job.scaffolding_template else None
            ),
            started_at=job.started_at,
            completed_at=job.completed_at,
            duration_seconds=job.duration_seconds,
            error_message=job.error_message,
            created_at=job.created_at,
        )
        for job in page_qs
    ]

    return PaginatedJobsSchema(
        items=items,
        total=total,
        page=page,
        per_page=per_page,
        pages=pages,
    )


@router.get("/jobs/{job_id}/", response=GenerationJobSchema)
def get_job(request, job_id: str):
    return get_object_or_404(
        GenerationJob.objects.select_related(
            "model",
            "app_requirement",
            "scaffolding_template",
            "batch",
            "created_by",
        ),
        id=job_id,
        created_by=request.auth,
    )


@router.post("/jobs/{job_id}/cancel/")
def cancel_job(request, job_id: str):
    job = get_object_or_404(GenerationJob, id=job_id, created_by=request.auth)
    if job.status in ("pending", "running"):
        job.status = GenerationJob.Status.CANCELLED
        job.save(update_fields=["status", "updated_at"])
        return {"success": True, "status": "cancelled"}
    return {
        "success": False,
        "status": job.status,
        "message": "Job cannot be cancelled",
    }


@router.get("/jobs/{job_id}/artifacts/", response=list[GenerationArtifactSchema])
def get_job_artifacts(request, job_id: str):
    job = get_object_or_404(GenerationJob, id=job_id, created_by=request.auth)
    return job.artifacts.all()


@router.get(
    "/jobs/{job_id}/copilot-iterations/",
    response=list[CopilotIterationSchema],
)
def get_copilot_iterations(request, job_id: str):
    job = get_object_or_404(GenerationJob, id=job_id, created_by=request.auth)
    return job.copilot_iterations.all()


@router.get("/jobs/{job_id}/export/")
def export_job(request, job_id: str):
    """Export full job data as JSON (job + artifacts + iterations)."""
    job = get_object_or_404(
        GenerationJob.objects.select_related(
            "model",
            "app_requirement",
            "scaffolding_template",
            "batch",
            "created_by",
        ),
        id=job_id,
        created_by=request.auth,
    )
    artifacts = list(
        job.artifacts.values(
            "id",
            "stage",
            "request_payload",
            "response_payload",
            "prompt_tokens",
            "completion_tokens",
            "total_cost",
            "created_at",
        ),
    )
    iterations = list(
        job.copilot_iterations.values(
            "id",
            "iteration_number",
            "action",
            "llm_request",
            "llm_response",
            "build_output",
            "build_success",
            "errors_detected",
            "fix_applied",
            "created_at",
        ),
    )
    return {
        "job": GenerationJobSchema.from_orm(job).dict(),
        "artifacts": artifacts,
        "copilot_iterations": iterations,
    }


# -- Batches ------------------------------------------------------------


@router.get("/batches/", response=list[GenerationBatchSchema])
def list_batches(request):
    return GenerationBatch.objects.filter(created_by=request.auth)


@router.get("/batches/{batch_id}/", response=GenerationBatchSchema)
def get_batch(request, batch_id: str):
    return get_object_or_404(GenerationBatch, id=batch_id, created_by=request.auth)


@router.get("/batches/{batch_id}/jobs/", response=list[GenerationJobListSchema])
def get_batch_jobs(request, batch_id: str):
    batch = get_object_or_404(
        GenerationBatch,
        id=batch_id,
        created_by=request.auth,
    )
    jobs = batch.jobs.select_related(
        "model",
        "app_requirement",
        "scaffolding_template",
    )
    return [
        GenerationJobListSchema(
            id=job.id,
            mode=job.mode,
            status=job.status,
            model_name=job.model.model_name if job.model else None,
            model_id_str=job.model.model_id if job.model else None,
            template_name=(job.app_requirement.name if job.app_requirement else None),
            scaffolding_name=(
                job.scaffolding_template.name if job.scaffolding_template else None
            ),
            started_at=job.started_at,
            completed_at=job.completed_at,
            duration_seconds=job.duration_seconds,
            error_message=job.error_message,
            created_at=job.created_at,
        )
        for job in jobs
    ]

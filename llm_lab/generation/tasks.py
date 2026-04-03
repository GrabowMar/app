"""Celery tasks for generation jobs."""

import logging

from celery import shared_task

logger = logging.getLogger(__name__)


@shared_task(bind=True, soft_time_limit=600, time_limit=660)
def run_generation_job(self, job_id: str) -> dict:
    """Execute a single generation job (any mode)."""
    from llm_lab.generation.models import GenerationJob  # noqa: PLC0415

    logger.info("Starting generation job %s", job_id)
    try:
        job = GenerationJob.objects.get(id=job_id)
    except GenerationJob.DoesNotExist:
        logger.exception("Job %s not found", job_id)
        return {"error": f"Job {job_id} not found"}

    # TODO: Implement generation orchestration per mode
    return {"job_id": str(job.id), "status": job.status}


@shared_task(bind=True)
def run_generation_batch(self, batch_id: str) -> dict:
    """Orchestrate a batch of generation jobs."""
    logger.info("Starting generation batch %s", batch_id)
    # TODO: Implement batch orchestration
    return {"batch_id": batch_id}


@shared_task(bind=True, soft_time_limit=300, time_limit=360)
def run_copilot_iteration(self, job_id: str, iteration: int) -> dict:
    """Execute a single copilot iteration."""
    logger.info("Copilot iteration %d for job %s", iteration, job_id)
    # TODO: Implement copilot iteration
    return {"job_id": job_id, "iteration": iteration}

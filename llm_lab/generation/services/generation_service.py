"""Generation orchestrator — executes generation jobs per mode."""

import json
import logging
import time

from django.utils import timezone

from llm_lab.generation.models import GenerationArtifact
from llm_lab.generation.models import GenerationJob
from llm_lab.generation.services.openrouter_client import OpenRouterClient
from llm_lab.generation.services.openrouter_client import OpenRouterError
from llm_lab.generation.services.prompt_renderer import PromptRenderer

logger = logging.getLogger(__name__)


class GenerationService:
    """Orchestrates generation for all three modes."""

    def __init__(self) -> None:
        self.client = OpenRouterClient()
        self.renderer = PromptRenderer()

    def execute(self, job: GenerationJob) -> None:
        """Execute a generation job based on its mode."""
        job.status = GenerationJob.Status.RUNNING
        job.started_at = timezone.now()
        job.save(update_fields=["status", "started_at", "updated_at"])

        try:
            if job.mode == GenerationJob.Mode.CUSTOM:
                self._run_custom(job)
            elif job.mode == GenerationJob.Mode.SCAFFOLDING:
                self._run_scaffolding(job)
            elif job.mode == GenerationJob.Mode.COPILOT:
                self._run_copilot(job)
            else:
                msg = f"Unknown mode: {job.mode}"
                raise ValueError(msg)

            job.status = GenerationJob.Status.COMPLETED
        except Exception as exc:
            logger.exception("Job %s failed", job.id)
            job.status = GenerationJob.Status.FAILED
            job.error_message = str(exc)[:2000]
        finally:
            job.completed_at = timezone.now()
            if job.started_at:
                job.duration_seconds = (
                    job.completed_at - job.started_at
                ).total_seconds()
            job.save(
                update_fields=[
                    "status",
                    "completed_at",
                    "duration_seconds",
                    "error_message",
                    "result_data",
                    "metrics",
                    "updated_at",
                ],
            )
            self._update_batch(job)

    # ── Custom Mode ───────────────────────────────────────────────────

    def _run_custom(self, job: GenerationJob) -> None:
        """Custom mode: direct system + user prompts → LLM."""
        model_id = job.model.model_id if job.model else "openai/gpt-4o-mini"
        messages = []
        if job.custom_system_prompt:
            messages.append({"role": "system", "content": job.custom_system_prompt})
        messages.append({"role": "user", "content": job.custom_user_prompt})

        start = time.time()
        response = self._call_llm(job, model_id, messages, stage="custom")
        elapsed = time.time() - start

        content = OpenRouterClient.extract_content(response)
        usage = OpenRouterClient.extract_usage(response)
        truncated = OpenRouterClient.is_truncated(response)

        job.result_data = {
            "content": content,
            "truncated": truncated,
            "finish_reason": response.get("choices", [{}])[0].get("finish_reason"),
        }
        job.metrics = {
            **usage,
            "duration_seconds": round(elapsed, 2),
            "model": model_id,
        }

    # ── Scaffolding Mode ──────────────────────────────────────────────

    def _run_scaffolding(self, job: GenerationJob) -> None:
        """Scaffolding mode: two-stage generation (backend → frontend)."""
        model_id = job.model.model_id if job.model else "openai/gpt-4o-mini"
        app_req = job.app_requirement
        if not app_req:
            msg = "Scaffolding mode requires an app requirement template"
            raise ValueError(msg)

        total_usage = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}

        # Stage 1: Backend generation
        backend_messages = self.renderer.render_backend_messages(
            app_requirement=app_req,
            prompt_template_system=job.backend_prompt_template,
            prompt_template_user=job.frontend_prompt_template,
        )
        start = time.time()
        backend_resp = self._call_llm(
            job, model_id, backend_messages, stage="backend",
        )
        backend_elapsed = time.time() - start
        backend_content = OpenRouterClient.extract_content(backend_resp)
        backend_usage = OpenRouterClient.extract_usage(backend_resp)
        for k in total_usage:
            total_usage[k] += backend_usage.get(k, 0)

        # Stage 2: Frontend generation (with backend context)
        frontend_messages = self.renderer.render_frontend_messages(
            app_requirement=app_req,
            backend_code=backend_content,
            prompt_template_system=job.backend_prompt_template,
            prompt_template_user=job.frontend_prompt_template,
        )
        start2 = time.time()
        frontend_resp = self._call_llm(
            job, model_id, frontend_messages, stage="frontend",
        )
        frontend_elapsed = time.time() - start2
        frontend_content = OpenRouterClient.extract_content(frontend_resp)
        frontend_usage = OpenRouterClient.extract_usage(frontend_resp)
        for k in total_usage:
            total_usage[k] += frontend_usage.get(k, 0)

        job.result_data = {
            "backend_code": backend_content,
            "frontend_code": frontend_content,
            "backend_truncated": OpenRouterClient.is_truncated(backend_resp),
            "frontend_truncated": OpenRouterClient.is_truncated(frontend_resp),
        }
        job.metrics = {
            **total_usage,
            "backend_duration": round(backend_elapsed, 2),
            "frontend_duration": round(frontend_elapsed, 2),
            "total_duration": round(backend_elapsed + frontend_elapsed, 2),
            "model": model_id,
        }

    # ── Copilot Mode ──────────────────────────────────────────────────

    def _run_copilot(self, job: GenerationJob) -> None:
        """Copilot mode: agentic generate→check loop (simplified)."""
        model_id = self._pick_copilot_model(job)

        system_prompt = (
            "You are an expert full-stack developer. Generate complete, "
            "working application code based on the user's description. "
            "Return well-structured code with clear file markers."
        )
        user_prompt = (
            f"Build the following application:\n\n{job.copilot_description}\n\n"
            "Generate a complete Flask backend (app.py) and React frontend (App.jsx). "
            "Make the code production-quality with proper error handling, "
            "rich data models, and a polished UI."
        )

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

        start = time.time()
        response = self._call_llm(job, model_id, messages, stage="copilot_iter_1")
        elapsed = time.time() - start

        content = OpenRouterClient.extract_content(response)
        usage = OpenRouterClient.extract_usage(response)

        job.copilot_current_iteration = 1
        job.result_data = {
            "content": content,
            "iterations_completed": 1,
            "truncated": OpenRouterClient.is_truncated(response),
        }
        job.metrics = {
            **usage,
            "duration_seconds": round(elapsed, 2),
            "model": model_id,
        }
        job.save(update_fields=["copilot_current_iteration", "updated_at"])

    # ── Helpers ────────────────────────────────────────────────────────

    def _call_llm(
        self,
        job: GenerationJob,
        model_id: str,
        messages: list[dict],
        *,
        stage: str,
    ) -> dict:
        """Call LLM and save the artifact."""
        request_payload = {
            "model": model_id,
            "messages": messages,
            "temperature": job.temperature,
            "max_tokens": job.max_tokens,
        }

        try:
            response = self.client.chat_completion(
                model=model_id,
                messages=messages,
                temperature=job.temperature,
                max_tokens=job.max_tokens,
            )
        except OpenRouterError:
            # Save failed artifact too
            GenerationArtifact.objects.create(
                job=job,
                stage=stage,
                request_payload=request_payload,
                response_payload={"error": "API call failed"},
            )
            raise

        usage = OpenRouterClient.extract_usage(response)
        GenerationArtifact.objects.create(
            job=job,
            stage=stage,
            request_payload=request_payload,
            response_payload=response,
            prompt_tokens=usage.get("prompt_tokens", 0),
            completion_tokens=usage.get("completion_tokens", 0),
        )
        return response

    @staticmethod
    def _pick_copilot_model(job: GenerationJob) -> str:
        """Choose model for copilot mode."""
        if job.model:
            return job.model.model_id
        # Default open-source models
        if job.copilot_use_open_source:
            return "deepseek/deepseek-chat-v3-0324:free"
        return "openai/gpt-4o-mini"

    @staticmethod
    def _update_batch(job: GenerationJob) -> None:
        """Update batch counters if job belongs to a batch."""
        if not job.batch:
            return
        batch = job.batch
        jobs = batch.jobs.all()
        batch.completed_jobs = jobs.filter(
            status=GenerationJob.Status.COMPLETED,
        ).count()
        batch.failed_jobs = jobs.filter(status=GenerationJob.Status.FAILED).count()
        done = batch.completed_jobs + batch.failed_jobs
        if done >= batch.total_jobs:
            if batch.failed_jobs == 0:
                batch.status = "completed"
            elif batch.completed_jobs == 0:
                batch.status = "failed"
            else:
                batch.status = "partial"
        elif done > 0:
            batch.status = "running"
        batch.save(
            update_fields=[
                "status",
                "completed_jobs",
                "failed_jobs",
                "updated_at",
            ],
        )

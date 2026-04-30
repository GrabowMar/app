"""Django Ninja API views for runtime container management."""

from __future__ import annotations

from typing import TYPE_CHECKING

from django.shortcuts import get_object_or_404
from ninja import Query
from ninja import Router

from llm_lab.common.pagination import paginate_queryset
from llm_lab.generation.models import GenerationJob
from llm_lab.runtime.api.schema import ActionListResponse
from llm_lab.runtime.api.schema import ContainerActionSchema
from llm_lab.runtime.api.schema import ContainerHealthResponse
from llm_lab.runtime.api.schema import ContainerInstanceSchema
from llm_lab.runtime.api.schema import ContainerListResponse
from llm_lab.runtime.api.schema import DockerInfo
from llm_lab.runtime.api.schema import GenericResponse
from llm_lab.runtime.models import ContainerAction
from llm_lab.runtime.models import ContainerInstance
from llm_lab.runtime.services import container_service
from llm_lab.runtime.services import docker_manager

if TYPE_CHECKING:
    from django.http import HttpRequest

router = Router(tags=["runtime"])


@router.get(
    "/docker/info/",
    response={200: DockerInfo, 503: GenericResponse},
)
def get_docker_info(request: HttpRequest):
    """Return Docker daemon availability and version info."""
    if not docker_manager.ping():
        return 503, GenericResponse(success=False, message="Docker daemon unavailable")
    c = docker_manager.client()
    info: dict = {}
    version: dict = {}
    try:
        info = c.info()
        version = c.version()
    except Exception:  # noqa: BLE001, S110
        pass  # best-effort; daemon_available already confirmed True
    return 200, DockerInfo(
        daemon_available=True,
        version=version.get("Version"),
        os=info.get("OSType"),
        arch=info.get("Architecture"),
    )


@router.get(
    "/containers/",
    response={200: ContainerListResponse},
)
def list_containers(
    request: HttpRequest,
    status: str | None = None,
    job_id: str | None = None,
    page: int = Query(1),
    per_page: int = Query(20),
):
    """List ContainerInstance rows with optional filters."""
    qs = ContainerInstance.objects.select_related("created_by", "generation_job")
    if status:
        qs = qs.filter(status=status)
    if job_id:
        qs = qs.filter(generation_job_id=job_id)
    items, total, page_num, total_pages = paginate_queryset(qs, page, per_page)
    return 200, ContainerListResponse(
        containers=list(items),
        pagination={
            "total": total,
            "page": page_num,
            "per_page": per_page,
            "total_pages": total_pages,
        },
    )


@router.get(
    "/containers/{container_id}/",
    response={200: ContainerInstanceSchema, 404: GenericResponse},
)
def get_container(request: HttpRequest, container_id: str):
    """Return detail for a single ContainerInstance."""
    instance = get_object_or_404(ContainerInstance, id=container_id)
    return 200, instance


@router.post(
    "/jobs/{job_id}/build/",
    response={200: ContainerInstanceSchema, 400: GenericResponse, 503: GenericResponse},
)
def build_container_for_job(request: HttpRequest, job_id: str):
    """Kick off a container build for the given generation job."""
    if not docker_manager.ping():
        return 503, GenericResponse(success=False, message="Docker daemon unavailable")
    job = get_object_or_404(GenerationJob, id=job_id)
    instance = container_service.build_for_job(job, request.user)
    return 200, instance


@router.post(
    "/containers/{container_id}/start/",
    response={200: ContainerActionSchema, 503: GenericResponse},
)
def start_container(request: HttpRequest, container_id: str):
    """Start a stopped container."""
    if not docker_manager.ping():
        return 503, GenericResponse(success=False, message="Docker daemon unavailable")
    instance = get_object_or_404(ContainerInstance, id=container_id)
    action = container_service.start_instance(instance, request.user)
    return 200, action


@router.post(
    "/containers/{container_id}/stop/",
    response={200: ContainerActionSchema, 503: GenericResponse},
)
def stop_container(request: HttpRequest, container_id: str):
    """Stop a running container."""
    if not docker_manager.ping():
        return 503, GenericResponse(success=False, message="Docker daemon unavailable")
    instance = get_object_or_404(ContainerInstance, id=container_id)
    action = container_service.stop_instance(instance, request.user)
    return 200, action


@router.post(
    "/containers/{container_id}/restart/",
    response={200: ContainerActionSchema, 503: GenericResponse},
)
def restart_container(request: HttpRequest, container_id: str):
    """Restart a container."""
    if not docker_manager.ping():
        return 503, GenericResponse(success=False, message="Docker daemon unavailable")
    instance = get_object_or_404(ContainerInstance, id=container_id)
    action = container_service.restart_instance(instance, request.user)
    return 200, action


@router.post(
    "/containers/{container_id}/remove/",
    response={200: ContainerActionSchema, 503: GenericResponse},
)
def remove_container(request: HttpRequest, container_id: str):
    """Remove a container (force=True)."""
    if not docker_manager.ping():
        return 503, GenericResponse(success=False, message="Docker daemon unavailable")
    instance = get_object_or_404(ContainerInstance, id=container_id)
    action = container_service.remove_instance(instance, request.user)
    return 200, action


@router.get(
    "/containers/{container_id}/logs/",
    response={200: str, 503: GenericResponse},
)
def get_container_logs(
    request: HttpRequest,
    container_id: str,
    tail: int = Query(200),
):
    """Return last *tail* lines of container logs as plain text."""
    if not docker_manager.ping():
        return 503, GenericResponse(success=False, message="Docker daemon unavailable")
    instance = get_object_or_404(ContainerInstance, id=container_id)
    output = docker_manager.logs(instance.name, tail=tail)
    return 200, output


@router.get(
    "/containers/{container_id}/health/",
    response={200: ContainerHealthResponse, 503: GenericResponse},
)
def get_container_health(request: HttpRequest, container_id: str):
    """Return current health state of a container."""
    if not docker_manager.ping():
        return 503, GenericResponse(success=False, message="Docker daemon unavailable")
    instance = get_object_or_404(ContainerInstance, id=container_id)
    data = docker_manager.health(instance.name)
    if "error" in data:
        return 503, GenericResponse(success=False, message=data["error"])
    return 200, ContainerHealthResponse(
        status=data.get("status", "unknown"),
        health=data.get("health", "unknown"),
        last_check=instance.last_health_check,
    )


@router.get(
    "/actions/",
    response={200: ActionListResponse},
)
def list_actions(
    request: HttpRequest,
    container_id: str | None = None,
    status: str | None = None,
    page: int = Query(1),
    per_page: int = Query(20),
):
    """List ContainerAction rows with optional filters."""
    qs = ContainerAction.objects.select_related("container", "triggered_by")
    if container_id:
        qs = qs.filter(container_id=container_id)
    if status:
        qs = qs.filter(status=status)
    items, total, page_num, total_pages = paginate_queryset(qs, page, per_page)
    return 200, ActionListResponse(
        actions=list(items),
        pagination={
            "total": total,
            "page": page_num,
            "per_page": per_page,
            "total_pages": total_pages,
        },
    )


@router.get(
    "/actions/{action_id}/",
    response={200: ContainerActionSchema, 404: GenericResponse},
)
def get_action(request: HttpRequest, action_id: str):
    """Return detail for a single ContainerAction."""
    action = get_object_or_404(ContainerAction, action_id=action_id)
    return 200, action

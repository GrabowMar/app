"""Pydantic schemas for the runtime API."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID  # noqa: TC003

from ninja import ModelSchema
from ninja import Schema

from llm_lab.runtime.models import ContainerAction
from llm_lab.runtime.models import ContainerInstance


class ContainerInstanceSchema(ModelSchema):
    id: UUID
    generation_job_id: UUID | None = None
    created_by_id: int | None = None

    class Meta:
        model = ContainerInstance
        fields = (
            "name",
            "image",
            "container_id",
            "status",
            "backend_port",
            "frontend_port",
            "health_status",
            "last_health_check",
            "config",
            "metadata",
            "created_at",
            "updated_at",
        )


class ContainerActionSchema(ModelSchema):
    id: UUID
    container_id: UUID | None = None
    triggered_by_id: int | None = None

    class Meta:
        model = ContainerAction
        fields = (
            "action_id",
            "action_type",
            "status",
            "progress_percent",
            "output",
            "error_message",
            "exit_code",
            "started_at",
            "completed_at",
            "created_at",
        )


class ContainerListResponse(Schema):
    containers: list[ContainerInstanceSchema]
    pagination: dict[str, int]


class ActionListResponse(Schema):
    actions: list[ContainerActionSchema]
    pagination: dict[str, int]


class DockerInfo(Schema):
    daemon_available: bool
    version: str | None = None
    os: str | None = None
    arch: str | None = None


class ContainerHealthResponse(Schema):
    status: str
    health: str
    last_check: datetime | None


class GenericResponse(Schema):
    success: bool
    message: str = ""


__all__ = [
    "ActionListResponse",
    "ContainerActionSchema",
    "ContainerHealthResponse",
    "ContainerInstanceSchema",
    "ContainerListResponse",
    "DockerInfo",
    "GenericResponse",
]

_ = (datetime,)

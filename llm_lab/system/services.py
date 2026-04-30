"""System monitoring and maintenance services."""

from __future__ import annotations

import time
from datetime import timedelta
from typing import Any

from django.core.cache import cache
from django.db import connection
from django.utils import timezone


# ---------------------------------------------------------------------------
# Host metrics
# ---------------------------------------------------------------------------


def host_metrics() -> dict[str, Any]:
    import psutil

    cpu_percent = psutil.cpu_percent(interval=0.2)
    mem = psutil.virtual_memory()
    load = psutil.getloadavg()
    boot_time = psutil.boot_time()
    uptime_seconds = time.time() - boot_time

    disks = []
    for part in psutil.disk_partitions(all=False):
        try:
            usage = psutil.disk_usage(part.mountpoint)
            disks.append(
                {
                    "mountpoint": part.mountpoint,
                    "device": part.device,
                    "fstype": part.fstype,
                    "total": usage.total,
                    "used": usage.used,
                    "free": usage.free,
                    "percent": usage.percent,
                }
            )
        except PermissionError:
            pass

    return {
        "cpu_percent": cpu_percent,
        "cpu_count": psutil.cpu_count(logical=True),
        "memory": {
            "total": mem.total,
            "used": mem.used,
            "available": mem.available,
            "percent": mem.percent,
        },
        "disks": disks,
        "load_avg": {"1m": load[0], "5m": load[1], "15m": load[2]},
        "uptime_seconds": uptime_seconds,
        "boot_time": boot_time,
    }


# ---------------------------------------------------------------------------
# Container health
# ---------------------------------------------------------------------------


def container_health() -> list[dict[str, Any]]:
    import docker

    try:
        client = docker.from_env()
        containers = client.containers.list(all=True)
        result = []
        for c in containers:
            health = "N/A"
            if c.attrs.get("State", {}).get("Health"):
                health = c.attrs["State"]["Health"].get("Status", "N/A")
            started = c.attrs.get("State", {}).get("StartedAt", "")
            result.append(
                {
                    "id": c.short_id,
                    "name": c.name,
                    "image": c.image.tags[0] if c.image.tags else str(c.image.short_id),
                    "status": c.status,
                    "started": started,
                    "health": health,
                }
            )
        return result
    except Exception as exc:
        return [{"error": str(exc)}]


# ---------------------------------------------------------------------------
# Redis status
# ---------------------------------------------------------------------------


def redis_status() -> dict[str, Any]:
    import redis as redis_lib
    from django.conf import settings

    url = getattr(settings, "REDIS_URL", "redis://redis:6379/0")
    try:
        client = redis_lib.from_url(url, socket_connect_timeout=2)
        start = time.monotonic()
        client.ping()
        latency_ms = round((time.monotonic() - start) * 1000, 2)
        info = client.info()
        return {
            "reachable": True,
            "ping_latency_ms": latency_ms,
            "connected_clients": info.get("connected_clients"),
            "used_memory_human": info.get("used_memory_human"),
            "total_commands_processed": info.get("total_commands_processed"),
            "redis_version": info.get("redis_version"),
        }
    except Exception as exc:
        return {"reachable": False, "error": str(exc)}


# ---------------------------------------------------------------------------
# Celery status
# ---------------------------------------------------------------------------


def celery_status() -> dict[str, Any]:
    import redis as redis_lib
    from celery import current_app as celery_app
    from django.conf import settings

    try:
        inspector = celery_app.control.inspect(timeout=2)
        active = inspector.active() or {}
        scheduled = inspector.scheduled() or {}
        reserved = inspector.reserved() or {}

        workers = list(active.keys())
        active_count = sum(len(v) for v in active.values())
        scheduled_count = sum(len(v) for v in scheduled.values())
        reserved_count = sum(len(v) for v in reserved.values())

        queue_lengths: dict[str, int] = {}
        try:
            url = getattr(settings, "REDIS_URL", "redis://redis:6379/0")
            rclient = redis_lib.from_url(url, socket_connect_timeout=2)
            for queue in ["celery", "default"]:
                length = rclient.llen(queue)
                if length:
                    queue_lengths[queue] = length
        except Exception:
            pass

        return {
            "reachable": True,
            "worker_count": len(workers),
            "workers": workers,
            "active_tasks": active_count,
            "scheduled_tasks": scheduled_count,
            "reserved_tasks": reserved_count,
            "queue_lengths": queue_lengths,
        }
    except Exception as exc:
        return {"reachable": False, "worker_count": 0, "error": str(exc)}


# ---------------------------------------------------------------------------
# DB stats
# ---------------------------------------------------------------------------


def db_stats() -> dict[str, Any]:
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT
                numbackends,
                xact_commit,
                xact_rollback,
                blks_hit,
                blks_read,
                tup_returned,
                tup_fetched,
                tup_inserted,
                tup_updated,
                tup_deleted,
                deadlocks
            FROM pg_stat_database
            WHERE datname = current_database()
            """
        )
        row = cursor.fetchone()
        cols = [
            "numbackends",
            "xact_commit",
            "xact_rollback",
            "blks_hit",
            "blks_read",
            "tup_returned",
            "tup_fetched",
            "tup_inserted",
            "tup_updated",
            "tup_deleted",
            "deadlocks",
        ]
        stat = dict(zip(cols, row)) if row else {}

        cursor.execute(
            """
            SELECT
                schemaname || '.' || tablename AS table_name,
                pg_total_relation_size(
                    (quote_ident(schemaname) || '.' || quote_ident(tablename))::regclass
                ) AS total_bytes
            FROM pg_tables
            WHERE schemaname NOT IN ('pg_catalog', 'information_schema')
            ORDER BY total_bytes DESC
            LIMIT 10
            """
        )
        top_tables = [
            {"table": r[0], "total_bytes": r[1], "total_human": _bytes_human(r[1])}
            for r in cursor.fetchall()
        ]

    return {"stats": stat, "top_tables_by_size": top_tables}


def _bytes_human(b: int) -> str:
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if b < 1024:
            return f"{b:.1f} {unit}"
        b /= 1024  # type: ignore[assignment]
    return f"{b:.1f} PB"


# ---------------------------------------------------------------------------
# App stats
# ---------------------------------------------------------------------------


def app_stats() -> dict[str, Any]:
    from llm_lab.analysis.models import AnalysisTask
    from llm_lab.generation.models import GenerationJob
    from llm_lab.reports.models import Report
    from llm_lab.runtime.models import ContainerInstance

    since = timezone.now() - timedelta(hours=24)

    def _counts(model, status_field="status"):
        qs = model.objects.values(status_field).order_by()
        counts = {row[status_field]: row["cnt"] for row in qs.annotate(cnt=__import__("django.db.models", fromlist=["Count"]).Count("pk"))}
        recent = model.objects.filter(created_at__gte=since).count() if hasattr(model, "created_at") else 0
        return {"by_status": counts, "last_24h": recent}

    from django.db.models import Count

    def _counts2(model):
        qs = model.objects.values("status").annotate(cnt=Count("pk")).order_by()
        by_status = {row["status"]: row["cnt"] for row in qs}
        recent = 0
        if hasattr(model, "created_at"):
            recent = model.objects.filter(created_at__gte=since).count()
        return {"by_status": by_status, "last_24h": recent}

    return {
        "analysis_tasks": _counts2(AnalysisTask),
        "generation_jobs": _counts2(GenerationJob),
        "reports": _counts2(Report),
        "container_instances": _counts2(ContainerInstance),
    }


# ---------------------------------------------------------------------------
# Maintenance actions
# ---------------------------------------------------------------------------


def clear_stuck_analysis_tasks(older_than_minutes: int = 60) -> int:
    from llm_lab.analysis.models import AnalysisTask

    threshold = timezone.now() - timedelta(minutes=older_than_minutes)
    updated = AnalysisTask.objects.filter(
        status__in=[AnalysisTask.Status.PENDING, AnalysisTask.Status.RUNNING],
        updated_at__lt=threshold,
    ).update(
        status=AnalysisTask.Status.FAILED,
        error_message=f"Marked failed by maintenance: stuck for >{older_than_minutes}m",
    )
    return updated


def clear_stuck_generation_jobs(older_than_minutes: int = 60) -> int:
    from llm_lab.generation.models import GenerationJob

    threshold = timezone.now() - timedelta(minutes=older_than_minutes)
    updated = GenerationJob.objects.filter(
        status__in=[GenerationJob.Status.PENDING, GenerationJob.Status.RUNNING],
        updated_at__lt=threshold,
    ).update(
        status=GenerationJob.Status.FAILED,
        error_message=f"Marked failed by maintenance: stuck for >{older_than_minutes}m",
    )
    return updated


def purge_orphan_containers() -> int:
    import docker

    from llm_lab.runtime.models import ContainerInstance

    try:
        client = docker.from_env()
        existing_ids = {c.id for c in client.containers.list(all=True)}
        existing_ids |= {c.short_id for c in client.containers.list(all=True)}
    except Exception:
        existing_ids = set()

    orphan_ids = []
    active_statuses = [
        ContainerInstance.Status.PENDING,
        ContainerInstance.Status.BUILDING,
        ContainerInstance.Status.RUNNING,
    ]
    candidates = ContainerInstance.objects.filter(status__in=active_statuses).exclude(
        container_id=""
    )
    for inst in candidates:
        cid = inst.container_id
        if cid not in existing_ids and not any(
            full_id.startswith(cid) for full_id in existing_ids
        ):
            orphan_ids.append(inst.pk)

    if orphan_ids:
        ContainerInstance.objects.filter(pk__in=orphan_ids).update(
            status=ContainerInstance.Status.REMOVED
        )

    return len(orphan_ids)


def clear_caches() -> dict[str, Any]:
    try:
        cache.clear()
        return {"success": True, "message": "All caches cleared"}
    except Exception as exc:
        return {"success": False, "error": str(exc)}

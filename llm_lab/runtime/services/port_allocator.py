"""Port allocation helpers for container instances."""

from __future__ import annotations

import logging

from llm_lab.runtime.models import ContainerInstance
from llm_lab.runtime.models import PortAllocation
from llm_lab.runtime.services import docker_manager

logger = logging.getLogger(__name__)

# Cap the retry loop so a misbehaving daemon can't spin forever.
_MAX_ALLOC_ATTEMPTS = 25


def allocate_pair(skip: set[int] | None = None) -> tuple[int, int]:
    """Allocate next free (backend_port, frontend_port) pair.

    Cross-checks docker's own published-port view so we don't hand out a
    port that's already bound by an orphaned or externally-managed container.

    ``skip`` is an optional set of host ports the caller knows are unusable
    (e.g. populated from previous ``PortBindError`` messages during a retry
    loop). The allocator treats them exactly like docker-bound ports.

    Critical: ``PortAllocation.allocate()`` runs ``socket.bind('127.0.0.1', …)``
    to detect free ports — but inside the django *container* that bind always
    succeeds because docker-proxy lives in the host netns, not ours. So we
    *cannot* rely on the bind check; the DB-uniqueness constraint + docker's
    port view + the caller-provided ``skip`` set are the only authoritative
    sources. On collision, we keep the colliding row reserved for the
    duration of the loop so subsequent calls skip it, then release the
    losers at the very end. Otherwise the same colliding pair would be
    handed out forever.
    """
    blocked: set[int] = set(skip or ())
    blocked |= docker_manager.list_bound_host_ports()
    losers: list[PortAllocation] = []
    winner: PortAllocation | None = None
    try:
        for _ in range(_MAX_ALLOC_ATTEMPTS):
            alloc = PortAllocation.allocate()
            if (
                alloc.backend_port not in blocked
                and alloc.frontend_port not in blocked
            ):
                winner = alloc
                return alloc.backend_port, alloc.frontend_port
            # Keep the row in DB so the next iteration's allocate() can't
            # pick the same pair (DB unique constraint blocks it).
            losers.append(alloc)
        # 25 attempts all collided — that's basically impossible unless the
        # host is saturated. Bail with the last allocation and let the
        # caller's PortBindError retry path scream loudly in the build log.
        if losers:
            winner = losers.pop()
            return winner.backend_port, winner.frontend_port
        # Should be unreachable, but keep the type checker happy.
        alloc = PortAllocation.allocate()
        winner = alloc
        return alloc.backend_port, alloc.frontend_port
    finally:
        for loser in losers:
            if winner is not None and loser.pk == winner.pk:
                continue
            try:
                loser.delete()
            except Exception:  # noqa: BLE001
                pass


def cleanup_orphan_allocations() -> int:
    """Drop DB ``PortAllocation`` rows whose container is gone or whose
    ports don't match docker's current view. Returns number deleted.

    Stale rows are the root cause of allocator collision loops: if a
    PortAllocation says ``5001/8001`` but the actual container is bound to
    ``5003/8003`` (because of an old retry), the allocator will keep
    skipping 5001/8001 forever even though they're really free, and keep
    handing out 5003/8003 which collide with the live container.
    """
    bound = docker_manager.list_bound_host_ports()
    deleted = 0
    for alloc in PortAllocation.objects.select_related("container").all():
        # No container attached at all → safe to drop.
        if alloc.container is None:
            try:
                alloc.delete()
                deleted += 1
            except Exception:  # noqa: BLE001
                pass
            continue
        # Container's recorded ports differ from the allocation row → drop.
        c = alloc.container
        if (
            c.backend_port
            and c.frontend_port
            and (
                c.backend_port != alloc.backend_port
                or c.frontend_port != alloc.frontend_port
            )
        ):
            try:
                alloc.delete()
                deleted += 1
            except Exception:  # noqa: BLE001
                pass
            continue
        # Container is "removed" / "failed" *and* the ports aren't actually
        # bound on the host → drop.
        if c.status in {"removed", "failed"} and (
            alloc.backend_port not in bound
            and alloc.frontend_port not in bound
        ):
            try:
                alloc.delete()
                deleted += 1
            except Exception:  # noqa: BLE001
                pass
    return deleted


def release(container: ContainerInstance) -> None:
    """Free the port allocation for a container."""
    try:
        alloc = container.port_allocation
        alloc.delete()
    except PortAllocation.DoesNotExist:
        pass
    except Exception:
        logger.exception("Failed to release ports for container %s", container.name)

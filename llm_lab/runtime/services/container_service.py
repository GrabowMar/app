"""Orchestrator for container lifecycle actions."""

from __future__ import annotations

import ast
import logging
import re
import tempfile
import threading
import time
import uuid
from pathlib import Path
from typing import TYPE_CHECKING

from django.db import connection
from django.db import transaction
from django.utils import timezone

from llm_lab.realtime import events as realtime
from llm_lab.runtime.models import ContainerAction
from llm_lab.runtime.models import ContainerInstance
from llm_lab.runtime.models import PortAllocation
from llm_lab.runtime.services import docker_manager
from llm_lab.runtime.services import port_allocator
from llm_lab.runtime.services.docker_manager import PortBindError

if TYPE_CHECKING:
    from llm_lab.generation.models import GenerationJob
    from llm_lab.users.models import User

logger = logging.getLogger(__name__)


def create_action(
    container: ContainerInstance,
    action_type: str,
    user: User | None = None,
) -> ContainerAction:
    """Persist a ContainerAction and dispatch it in a daemon thread."""
    action = ContainerAction.objects.create(
        action_id=f"act_{uuid.uuid4().hex[:12]}",
        container=container,
        action_type=action_type,
        status=ContainerAction.Status.PENDING,
        triggered_by=user,
    )
    _dispatch(action.id)
    return action


def _dispatch(action_id) -> None:
    thread = threading.Thread(
        target=_execute,
        args=(action_id,),
        daemon=True,
        name=f"container-action-{action_id}",
    )
    thread.start()


def _execute(action_id) -> None:
    try:
        with transaction.atomic():
            action = ContainerAction.objects.select_for_update().get(id=action_id)
            if action.status != ContainerAction.Status.PENDING:
                return
            action.mark_running()

        container = action.container
        if container is None:
            action.mark_failed("Container no longer exists")
            return

        action_type = action.action_type

        if action_type == ContainerAction.ActionType.BUILD:
            _do_build(action, container)
        elif action_type == ContainerAction.ActionType.START:
            _do_start(action, container)
        elif action_type == ContainerAction.ActionType.STOP:
            _do_stop(action, container)
        elif action_type == ContainerAction.ActionType.RESTART:
            _do_restart(action, container)
        elif action_type == ContainerAction.ActionType.REMOVE:
            _do_remove(action, container)
        elif action_type == ContainerAction.ActionType.LOGS:
            _do_logs(action, container)
        elif action_type == ContainerAction.ActionType.HEALTH:
            _do_health(action, container)
        else:
            action.mark_failed(f"Unknown action type: {action_type}")

    except ContainerAction.DoesNotExist:
        logger.warning("ContainerAction %s vanished before execution", action_id)
    except Exception as exc:
        logger.exception("ContainerAction %s failed unexpectedly", action_id)
        try:
            a = ContainerAction.objects.get(id=action_id)
            if a.status in (
                ContainerAction.Status.PENDING,
                ContainerAction.Status.RUNNING,
            ):
                a.mark_failed(str(exc))
        except ContainerAction.DoesNotExist:
            pass
    finally:
        connection.close()


def _do_build(action: ContainerAction, container: ContainerInstance) -> None:
    if not docker_manager.ping():
        action.mark_failed("Docker daemon unavailable")
        container.status = ContainerInstance.Status.FAILED
        container.save(update_fields=["status"])
        return

    container.status = ContainerInstance.Status.BUILDING
    container.save(update_fields=["status"])
    action.update_progress(10)
    realtime.publish(
        f"runtime:{container.id}",
        {
            "type": "status",
            "status": container.status,
            "updated_at": timezone.now().isoformat(),
        },
    )

    job = container.generation_job
    tag = f"llm_lab/{container.name}:latest"

    build_log: list[str] = []
    last_flush = [time.monotonic()]
    log_channel = f"runtime:{container.id}:log"

    def _flush(force: bool = False) -> None:
        """Persist tail to action.output, throttled to ~2 writes/sec.

        We also publish each line on a realtime channel for live tail; the
        DB write is purely for users that load the page after the build.
        """
        now = time.monotonic()
        if not force and (now - last_flush[0]) < 0.5:
            return
        last_flush[0] = now
        try:
            action.output = "\n".join(build_log[-400:])
            action.save(update_fields=["output"])
        except Exception:  # noqa: BLE001
            pass

    def _log(line: str) -> None:
        build_log.append(line)
        try:
            realtime.publish(log_channel, {"type": "log", "line": line})
        except Exception:  # noqa: BLE001
            pass
        _flush()

    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            build_path = Path(tmpdir)
            if job is not None:
                from llm_lab.runtime.services.scaffolding import prepare_build_dir

                prepare_build_dir(job, build_path, app_base=container.app_path() or "/")
            else:
                _write_minimal_dockerfile(build_path)

            # Cheap pre-build sanity check: try to parse backend Python so
            # we surface a clean SyntaxError before paying for docker build.
            _maybe_validate_python(build_path, _log)

            action.update_progress(40)
            docker_manager.build_image(str(build_path), tag, log_sink=_log)

        container.image = tag
        action.update_progress(70)
        _flush(force=True)

        # Best-effort: if a container with our reserved name already exists
        # (typical after a previous failed start or manual rebuild), remove
        # it so docker.run() doesn't 409 with "name already in use".
        try:
            existing = docker_manager.client()
            if existing is not None:
                try:
                    old = existing.containers.get(container.name)
                    old.remove(force=True)
                    _log(f"removed stale container {container.name}")
                except Exception:  # noqa: BLE001
                    pass
        except Exception:  # noqa: BLE001
            pass

        cid = _run_with_port_retry(container, tag, _log)
        container.container_id = cid
        container.status = ContainerInstance.Status.RUNNING
        container.save(update_fields=["image", "container_id", "status"])
        action.update_progress(100)
        _flush(force=True)
        tail = "\n".join(build_log[-200:])
        summary = f"Built {tag}, container {cid}"
        action.mark_completed(
            output=f"{summary}\n--- build log (tail) ---\n{tail}" if tail else summary,
            exit_code=0,
        )
        realtime.publish(
            f"runtime:{container.id}",
            {
                "type": "status",
                "status": container.status,
                "updated_at": timezone.now().isoformat(),
            },
        )

    except Exception as exc:
        logger.exception("Build failed for %s", container.name)
        container.status = ContainerInstance.Status.FAILED
        container.save(update_fields=["status"])
        _flush(force=True)
        tail = "\n".join(build_log[-400:])
        err = str(exc)
        full = f"{err}\n--- build log (tail) ---\n{tail}" if tail else err
        try:
            action.output = full
            action.save(update_fields=["output"])
        except Exception:  # noqa: BLE001
            pass
        action.mark_failed(full[:8000])
        realtime.publish(
            f"runtime:{container.id}",
            {
                "type": "status",
                "status": container.status,
                "updated_at": timezone.now().isoformat(),
            },
        )


def _maybe_validate_python(build_path: Path, log) -> None:
    """If a Python backend entry exists in the build context, parse it.

    We check a few well-known locations (matches the templates currently
    shipped). On SyntaxError we raise — the caller's exception handler
    will persist the error with full transcript. On any other issue we
    silently skip so we never block builds for valid-but-exotic layouts.
    """
    candidates = [
        build_path / "backend" / "app.py",
        build_path / "app.py",
        build_path / "main.py",
    ]
    for path in candidates:
        if not path.exists():
            continue
        try:
            source = path.read_text()
        except Exception:  # noqa: BLE001
            return
        try:
            ast.parse(source, filename=str(path))
        except SyntaxError as exc:
            log(f"pre-build: backend SyntaxError in {path.name}: {exc}")
            msg = (
                f"Backend Python failed to parse before build: "
                f"{path.name}:{exc.lineno}:{exc.offset}: {exc.msg}"
            )
            raise RuntimeError(msg) from exc
        return


def _evict_orphan_holding(host_port: int, log) -> None:
    """If any docker container (not necessarily ours) is bound to ``host_port``,
    stop+remove it so we can take the port. We only ever evict containers
    labelled ``llm_lab.managed=true`` — never random user containers.
    """
    cli = docker_manager.client()
    if cli is None:
        return
    try:
        for ct in cli.containers.list(all=False):
            labels = (ct.attrs or {}).get("Config", {}).get("Labels") or {}
            if labels.get("llm_lab.managed") != "true":
                continue
            pmap = (ct.attrs or {}).get("NetworkSettings", {}).get("Ports") or {}
            for _key, bindings in pmap.items():
                if not bindings:
                    continue
                for b in bindings:
                    try:
                        hp = int(b.get("HostPort") or 0)
                    except (TypeError, ValueError):
                        continue
                    if hp == host_port:
                        log(
                            f"evicting orphan container {ct.name} holding "
                            f"port {host_port}",
                        )
                        try:
                            ct.remove(force=True)
                        except Exception as exc:  # noqa: BLE001
                            log(f"  eviction failed: {exc}")
                        return
    except Exception as exc:  # noqa: BLE001
        log(f"orphan eviction scan failed: {exc}")


_PORT_BIND_RE = re.compile(r"(?:Bind for\s+)?(?:\d{1,3}\.){3}\d{1,3}:(\d{2,5})")


def _extract_bound_ports(exc: BaseException) -> set[int]:
    """Pull host port numbers out of a docker PortBindError message.

    Examples we parse:
      "Bind for 127.0.0.1:8003 failed: port is already allocated"
      "0.0.0.0:5001: bind: address already in use"
    Anything we can't parse → empty set (caller falls back to eviction +
    cleanup heuristics).
    """
    found: set[int] = set()
    msg = str(exc)
    for m in _PORT_BIND_RE.finditer(msg):
        try:
            found.add(int(m.group(1)))
        except (TypeError, ValueError):
            continue
    return found


def _run_with_port_retry(
    container: ContainerInstance,
    tag: str,
    log,
) -> str:
    """Call ``docker_manager.run_container``; on host-port collision retry
    up to 3 times, evicting stale ``llm_lab.managed`` orphans and asking
    the allocator (after a stale-row cleanup) for a fresh pair.

    Every port that produces a ``PortBindError`` gets added to a per-build
    ``skip_ports`` set so the next allocation can't re-pick it — important
    for non-docker host listeners which are invisible to both
    ``list_bound_host_ports`` (docker-only) and ``socket.bind`` (different
    netns inside the django container).
    """
    max_attempts = 3
    skip_ports: set[int] = set()
    for attempt in range(max_attempts):
        ports: dict[str, tuple[str, int] | int] = {}
        env: dict[str, str] = {}
        if container.backend_port:
            ports["5000/tcp"] = ("127.0.0.1", container.backend_port)
            env["BACKEND_PORT"] = "5000"
        if container.frontend_port:
            ports["80/tcp"] = ("127.0.0.1", container.frontend_port)
        try:
            return docker_manager.run_container(
                tag,
                container.name,
                ports,
                env,
                str(container.id),
            )
        except PortBindError as exc:
            if attempt >= max_attempts - 1:
                raise
            # Block the specific bound port(s) parsed from the docker error
            # — covers non-docker host listeners the daemon view can't see.
            parsed = _extract_bound_ports(exc)
            if parsed:
                skip_ports |= parsed
                log(f"blocking ports {sorted(parsed)} for remainder of build")
            else:
                # Couldn't parse — block our currently-assigned pair so we
                # at least don't re-pick the same ones blindly.
                if container.backend_port:
                    skip_ports.add(container.backend_port)
                if container.frontend_port:
                    skip_ports.add(container.frontend_port)
            log(f"port bind collision (attempt {attempt + 1}): {exc}; re-allocating")
            # Best-effort: evict any llm_lab-managed orphan holding our ports.
            for hp in (container.backend_port, container.frontend_port):
                if hp:
                    _evict_orphan_holding(hp, log)
            # Drop stale DB rows so the allocator's "next free" search
            # actually advances past dead allocations.
            try:
                deleted = port_allocator.cleanup_orphan_allocations()
                if deleted:
                    log(f"cleaned up {deleted} orphan port allocation row(s)")
            except Exception as exc2:  # noqa: BLE001
                log(f"orphan cleanup failed: {exc2}")
            # Release current allocation row for this container, pick fresh
            # — passing the accumulated skip set so we don't re-pick a known
            # bad port (e.g. one held by a non-docker host process).
            try:
                port_allocator.release(container)
            except Exception:  # noqa: BLE001
                pass
            new_be, new_fe = port_allocator.allocate_pair(skip=skip_ports)
            container.backend_port = new_be
            container.frontend_port = new_fe
            container.save(update_fields=["backend_port", "frontend_port"])
            try:
                alloc = PortAllocation.objects.get(
                    backend_port=new_be, frontend_port=new_fe,
                )
                alloc.container = container
                alloc.save(update_fields=["container"])
            except PortAllocation.DoesNotExist:
                pass
            # Nuke our own half-created container row if docker left one.
            try:
                cli = docker_manager.client()
                if cli is not None:
                    try:
                        cli.containers.get(container.name).remove(force=True)
                    except Exception:  # noqa: BLE001
                        pass
            except Exception:  # noqa: BLE001
                pass
    msg = "exhausted port-bind retries"
    raise RuntimeError(msg)


def _write_minimal_dockerfile(path: Path) -> None:
    (path / "Dockerfile").write_text(
        'FROM python:3.11-slim\nWORKDIR /app\nCOPY . .\nRUN pip install flask --quiet\nCMD ["python", "app.py"]\n',
    )
    (path / "app.py").write_text(
        "from flask import Flask, jsonify\n"
        "app = Flask(__name__)\n\n"
        "@app.route('/api/health')\n"
        "def health():\n"
        "    return jsonify({'status': 'ok'})\n\n"
        "if __name__ == '__main__':\n"
        "    app.run(host='0.0.0.0', port=5000)\n",
    )


def _do_start(action: ContainerAction, container: ContainerInstance) -> None:
    result = docker_manager.start(container.name)
    if "error" in result:
        action.mark_failed(result["error"])
    else:
        container.status = ContainerInstance.Status.RUNNING
        container.save(update_fields=["status"])
        action.mark_completed(output="Started", exit_code=0)
        realtime.publish(
            f"runtime:{container.id}",
            {
                "type": "status",
                "status": container.status,
                "updated_at": timezone.now().isoformat(),
            },
        )


def _do_stop(action: ContainerAction, container: ContainerInstance) -> None:
    result = docker_manager.stop(container.name)
    if "error" in result:
        action.mark_failed(result["error"])
    else:
        container.status = ContainerInstance.Status.STOPPED
        container.save(update_fields=["status"])
        action.mark_completed(output="Stopped", exit_code=0)
        realtime.publish(
            f"runtime:{container.id}",
            {
                "type": "status",
                "status": container.status,
                "updated_at": timezone.now().isoformat(),
            },
        )


def _do_restart(action: ContainerAction, container: ContainerInstance) -> None:
    result = docker_manager.restart(container.name)
    if "error" in result:
        action.mark_failed(result["error"])
    else:
        container.status = ContainerInstance.Status.RUNNING
        container.save(update_fields=["status"])
        action.mark_completed(output="Restarted", exit_code=0)
        realtime.publish(
            f"runtime:{container.id}",
            {
                "type": "status",
                "status": container.status,
                "updated_at": timezone.now().isoformat(),
            },
        )


def _do_remove(action: ContainerAction, container: ContainerInstance) -> None:
    result = docker_manager.remove(container.name)
    if "error" in result:
        action.mark_failed(result["error"])
    else:
        port_allocator.release(container)
        container.status = ContainerInstance.Status.REMOVED
        container.save(update_fields=["status"])
        action.mark_completed(output="Removed", exit_code=0)
        realtime.publish(
            f"runtime:{container.id}",
            {
                "type": "status",
                "status": container.status,
                "updated_at": timezone.now().isoformat(),
            },
        )


def _do_logs(action: ContainerAction, container: ContainerInstance) -> None:
    output = docker_manager.logs(container.name)
    action.mark_completed(output=output, exit_code=0)


def _do_health(action: ContainerAction, container: ContainerInstance) -> None:
    data = docker_manager.health(container.name)
    if "error" in data:
        action.mark_failed(data["error"])
    else:
        container.health_status = data.get("health", "")
        container.last_health_check = timezone.now()
        container.save(update_fields=["health_status", "last_health_check"])
        action.mark_completed(
            output=f"status={data.get('status')} health={data.get('health')}",
            exit_code=0,
        )


def _allocate_subdomain(job: GenerationJob | None) -> str:
    """Pick a stable URL slug. Prefers job.id.hex[:8], lengthens on collision."""
    seed_hex = (job.id.hex if job is not None else uuid.uuid4().hex)
    for length in range(8, 13):
        candidate = seed_hex[:length]
        if not ContainerInstance.objects.filter(subdomain=candidate).exists():
            return candidate
    # Fall back to a fresh uuid prefix
    return uuid.uuid4().hex[:12]


def build_for_job(job: GenerationJob, user: User | None) -> ContainerInstance:
    """Create a ContainerInstance for *job* and kick off a build action."""
    backend_port, frontend_port = port_allocator.allocate_pair()
    slug = f"llm-{uuid.uuid4().hex[:8]}"
    subdomain = _allocate_subdomain(job)

    instance = ContainerInstance.objects.create(
        generation_job=job,
        name=slug,
        status=ContainerInstance.Status.PENDING,
        backend_port=backend_port,
        frontend_port=frontend_port,
        subdomain=subdomain,
        created_by=user,
    )

    try:
        alloc = PortAllocation.objects.get(
            backend_port=backend_port,
            frontend_port=frontend_port,
        )
        alloc.container = instance
        alloc.save(update_fields=["container"])
    except PortAllocation.DoesNotExist:
        pass

    create_action(instance, ContainerAction.ActionType.BUILD, user)
    return instance


def stop_instance(container: ContainerInstance, user: User | None) -> ContainerAction:
    return create_action(container, ContainerAction.ActionType.STOP, user)


def start_instance(
    container: ContainerInstance,
    user: User | None,
) -> ContainerAction:
    return create_action(container, ContainerAction.ActionType.START, user)


def restart_instance(
    container: ContainerInstance,
    user: User | None,
) -> ContainerAction:
    return create_action(container, ContainerAction.ActionType.RESTART, user)


def remove_instance(
    container: ContainerInstance,
    user: User | None,
) -> ContainerAction:
    return create_action(container, ContainerAction.ActionType.REMOVE, user)

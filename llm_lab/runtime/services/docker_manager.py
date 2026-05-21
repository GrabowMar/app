"""Thin wrapper around the Docker SDK."""

from __future__ import annotations

import logging
import os
from typing import Any

logger = logging.getLogger(__name__)

_docker_client = None


class PortBindError(RuntimeError):
    """Raised when docker.run() fails because a host port is already bound.

    Caught by ``container_service._do_build`` so it can pick a fresh port
    and retry once before giving up.
    """


def _is_port_bind_error(exc: BaseException) -> bool:
    msg = str(exc).lower()
    return (
        "address already in use" in msg
        or "port is already allocated" in msg
        or "bind for" in msg and "failed" in msg
    )


def client():
    """Return a cached Docker client, or None if daemon unavailable."""
    global _docker_client  # noqa: PLW0603
    if _docker_client is not None:
        return _docker_client
    try:
        import docker

        _docker_client = docker.from_env()
    except Exception as exc:  # noqa: BLE001
        logger.warning("Docker client unavailable: %s", exc)
        return None
    else:
        return _docker_client


def ping() -> bool:
    """Return True if the Docker daemon is reachable."""
    try:
        c = client()
        if c is None:
            return False
        c.ping()
        return True
    except Exception:  # noqa: BLE001
        return False


def build_image(
    path: str,
    tag: str,
    dockerfile: str | None = None,
    log_sink: Any = None,
):
    """Build a Docker image from the given directory.

    Returns the image object on success, raises on failure. If *log_sink* is
    provided it is called with each streamed log line so callers (e.g. the
    container service) can persist the build transcript on ContainerAction
    for the UI to display when a build fails.
    """
    c = client()
    if c is None:
        msg = "Docker daemon unavailable"
        raise ConnectionError(msg)

    # Use the low-level streaming API so we capture per-step output. The
    # default high-level images.build() swallows interleaved stdout/stderr
    # and surfaces only a terse "command returned non-zero code" message.
    import json as _json

    api = c.api
    kwargs: dict[str, Any] = {"path": path, "tag": tag, "rm": True, "decode": True}
    if dockerfile:
        kwargs["dockerfile"] = dockerfile

    last_image_id: str | None = None
    captured: list[str] = []
    partial: list[str] = [""]  # buffer for line that hasn't ended with \n yet

    def _emit(line: str) -> None:
        captured.append(line)
        if log_sink is not None:
            try:
                log_sink(line)
            except Exception:  # noqa: BLE001
                pass

    def _consume(text: str) -> None:
        """Split *text* on newlines, joining partial leftovers across chunks."""
        if not text:
            return
        text = partial[0] + text
        parts = text.split("\n")
        # Last element may be incomplete; keep it for the next chunk.
        partial[0] = parts[-1]
        for ln in parts[:-1]:
            if ln.strip():
                _emit(ln)

    for chunk in api.build(**kwargs):
        if not isinstance(chunk, dict):
            continue
        if "stream" in chunk:
            _consume(str(chunk["stream"]))
            m = chunk.get("aux") or {}
            if isinstance(m, dict) and m.get("ID"):
                last_image_id = m["ID"]
        elif "aux" in chunk and isinstance(chunk["aux"], dict):
            if chunk["aux"].get("ID"):
                last_image_id = chunk["aux"]["ID"]
        elif "errorDetail" in chunk or "error" in chunk:
            err = chunk.get("error") or _json.dumps(chunk.get("errorDetail") or {})
            # Flush whatever partial line we held before reporting.
            if partial[0].strip():
                _emit(partial[0].rstrip())
                partial[0] = ""
            _emit(f"ERROR: {err}")
            transcript = "\n".join(captured[-400:])
            raise RuntimeError(f"docker build failed: {err}\n--- build log ---\n{transcript}")
        elif "status" in chunk:
            _consume(str(chunk["status"]) + "\n")

    # Flush any trailing partial line so the tail isn't cut mid-message.
    if partial[0].strip():
        _emit(partial[0].rstrip())
        partial[0] = ""

    if last_image_id:
        try:
            return c.images.get(last_image_id)
        except Exception:  # noqa: BLE001
            pass
    try:
        return c.images.get(tag)
    except Exception:  # noqa: BLE001
        return None


def run_container(
    image: str,
    name: str,
    ports: dict[str, int],
    env: dict[str, str],
    container_instance_id: str = "",
) -> str:
    """Start a container and return its container ID.

    Raises :class:`PortBindError` when the failure is specifically a host-port
    collision so the caller can re-pick a port and retry.
    """
    c = client()
    if c is None:
        msg = "Docker daemon unavailable"
        raise ConnectionError(msg)
    # The django/celery containers must be able to reach the spawned app
    # container so the /app/<id>/ proxy works. Default to the same docker
    # network django is on; falls back to "bridge" for plain-host installs.
    network = os.environ.get("LLM_LAB_APP_NETWORK", "bridge")
    try:
        container = c.containers.run(
            image,
            name=name,
            ports=ports,
            environment=env,
            detach=True,
            cap_drop=["ALL"],
            read_only=False,
            mem_limit="512m",
            cpu_period=100000,
            cpu_quota=50000,
            network=network,
            labels={
                "llm_lab.managed": "true",
                "llm_lab.instance_id": container_instance_id,
            },
        )
    except Exception as exc:  # noqa: BLE001
        if _is_port_bind_error(exc):
            raise PortBindError(str(exc)) from exc
        raise
    return container.id


def list_bound_host_ports() -> set[int]:
    """Return the set of host ports currently published by ANY container.

    Used by the port allocator to avoid handing out a port that is already
    bound on the host even if our DB doesn't know about it (e.g. orphaned
    containers, manually-started ones, or other apps on the same machine).
    Returns an empty set if the daemon is unavailable — callers should treat
    that as "no information, proceed".
    """
    c = client()
    if c is None:
        return set()
    bound: set[int] = set()
    try:
        for ct in c.containers.list(all=False):
            pmap = (ct.attrs or {}).get("NetworkSettings", {}).get("Ports") or {}
            for _key, bindings in pmap.items():
                if not bindings:
                    continue
                for b in bindings:
                    try:
                        bound.add(int(b.get("HostPort") or 0))
                    except (TypeError, ValueError):
                        continue
    except Exception as exc:  # noqa: BLE001
        logger.warning("list_bound_host_ports failed: %s", exc)
    bound.discard(0)
    return bound


def stop(name: str) -> dict[str, Any]:
    """Stop a running container by name."""
    try:
        c = client()
        if c is None:
            return {"error": "Docker daemon unavailable"}
        container = c.containers.get(name)
        container.stop(timeout=10)
    except Exception as exc:  # noqa: BLE001
        logger.warning("stop(%s) failed: %s", name, exc)
        return {"error": str(exc)}
    else:
        return {"status": "stopped"}


def start(name: str) -> dict[str, Any]:
    """Start a stopped container by name."""
    try:
        c = client()
        if c is None:
            return {"error": "Docker daemon unavailable"}
        container = c.containers.get(name)
        container.start()
    except Exception as exc:  # noqa: BLE001
        logger.warning("start(%s) failed: %s", name, exc)
        return {"error": str(exc)}
    else:
        return {"status": "started"}


def restart(name: str) -> dict[str, Any]:
    """Restart a container by name."""
    try:
        c = client()
        if c is None:
            return {"error": "Docker daemon unavailable"}
        container = c.containers.get(name)
        container.restart(timeout=10)
    except Exception as exc:  # noqa: BLE001
        logger.warning("restart(%s) failed: %s", name, exc)
        return {"error": str(exc)}
    else:
        return {"status": "restarted"}


def remove(name: str, *, force: bool = True) -> dict[str, Any]:
    """Remove a container by name."""
    try:
        c = client()
        if c is None:
            return {"error": "Docker daemon unavailable"}
        container = c.containers.get(name)
        container.remove(force=force)
    except Exception as exc:  # noqa: BLE001
        logger.warning("remove(%s) failed: %s", name, exc)
        return {"error": str(exc)}
    else:
        return {"status": "removed"}


def logs(name: str, tail: int = 200) -> str:
    """Fetch last *tail* lines of logs from a container."""
    try:
        c = client()
        if c is None:
            return "Docker daemon unavailable"
        container = c.containers.get(name)
        raw = container.logs(tail=tail, stream=False)
    except Exception as exc:  # noqa: BLE001
        logger.warning("logs(%s) failed: %s", name, exc)
        return f"Error fetching logs: {exc}"
    else:
        if isinstance(raw, bytes):
            return raw.decode("utf-8", errors="replace")
        return str(raw)


def inspect(name: str) -> dict[str, Any]:
    """Return low-level container info."""
    try:
        c = client()
        if c is None:
            return {"error": "Docker daemon unavailable"}
        container = c.containers.get(name)
    except Exception as exc:  # noqa: BLE001
        logger.warning("inspect(%s) failed: %s", name, exc)
        return {"error": str(exc)}
    else:
        return container.attrs or {}


def exec_in(name: str, cmd: list[str], timeout_s: int = 10) -> dict[str, Any]:
    """Run a short command inside a running container; return exit_code + output."""
    try:
        c = client()
        if c is None:
            return {"error": "Docker daemon unavailable", "exit_code": -1, "output": ""}
        container = c.containers.get(name)
        result = container.exec_run(cmd, demux=False, tty=False)
    except Exception as exc:  # noqa: BLE001
        logger.warning("exec_in(%s, %s) failed: %s", name, cmd, exc)
        return {"error": str(exc), "exit_code": -1, "output": ""}
    out = result.output
    if isinstance(out, bytes):
        out = out.decode("utf-8", errors="replace")
    return {"exit_code": int(result.exit_code or 0), "output": out or ""}


def health(name: str) -> dict[str, Any]:
    """Return container health state."""
    try:
        c = client()
        if c is None:
            return {"error": "Docker daemon unavailable"}
        container = c.containers.get(name)
        state = (container.attrs or {}).get("State", {})
        health_info = state.get("Health", {})
        return {
            "status": container.status,
            "health": health_info.get("Status", "unknown"),
        }
    except Exception as exc:  # noqa: BLE001
        logger.warning("health(%s) failed: %s", name, exc)
        return {"error": str(exc)}


def list_managed() -> list[dict[str, Any]]:
    """List containers managed by llm_lab (label filter)."""
    try:
        c = client()
        if c is None:
            return []
        containers = c.containers.list(
            all=True,
            filters={"label": "llm_lab.managed=true"},
        )
        return [
            {
                "id": ct.short_id,
                "name": ct.name,
                "status": ct.status,
                "labels": ct.labels,
            }
            for ct in containers
        ]
    except Exception as exc:  # noqa: BLE001
        logger.warning("list_managed failed: %s", exc)
        return []

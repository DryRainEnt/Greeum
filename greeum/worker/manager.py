"""Utilities for managing the persistent Greeum worker daemon."""

from __future__ import annotations

import json
import logging
import os
import socket
import subprocess
import sys
import time
import urllib.parse
from datetime import datetime
from pathlib import Path
from typing import Optional

from .client import resolve_endpoint, WriteServiceClient, WorkerUnavailableError
from ..config_store import DEFAULT_ST_MODEL

DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8820
MAX_PORT = 8840
HEALTH_TIMEOUT = float(os.getenv("GREEUM_WORKER_HEALTH_TIMEOUT", "1.0"))
START_TIMEOUT = float(os.getenv("GREEUM_WORKER_START_TIMEOUT", "30.0"))

logger = logging.getLogger("greeum.worker.manager")


def _find_free_port(start: int = DEFAULT_PORT, end: int = MAX_PORT) -> int:
    for port in range(start, end + 1):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            try:
                sock.bind((DEFAULT_HOST, port))
                return port
            except OSError:
                continue
    raise RuntimeError("No free port available for worker")


def _healthcheck(endpoint: str, timeout: float = HEALTH_TIMEOUT) -> bool:
    import urllib.request

    parsed = urllib.parse.urlparse(endpoint)
    path = parsed.path or "/mcp"
    if path.endswith("/mcp"):
        path = path[: -len("/mcp")] + "/healthz"
    else:
        path = "/healthz"
    health_url = (f"{parsed.scheme}://{parsed.netloc}{path}" if parsed.scheme else path)
    try:
        with urllib.request.urlopen(health_url, timeout=timeout) as response:
            return response.status == 200
    except Exception:  # noqa: BLE001 - worker not ready/offline
        return False


def _default_state_path(data_dir: Path) -> Path:
    return data_dir / "worker_state.json"


def _read_state(path: Path) -> Optional[dict]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return None
    except json.JSONDecodeError:
        return None


def _write_state(path: Path, data: dict) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def _warmup_worker(endpoint: str, semantic: bool) -> None:
    if not semantic:
        return

    model_name = os.environ.get("GREEUM_ST_MODEL", DEFAULT_ST_MODEL)
    try:
        client = WriteServiceClient(endpoint)
        client.call("warmup_embeddings", {"model": model_name})
        logger.info("Worker warm-up successful (%s)", model_name)
    except WorkerUnavailableError as exc:  # pragma: no cover - network race
        logger.warning("Worker warm-up unavailable: %s", exc)
    except Exception as exc:  # pragma: no cover - non-fatal
        logger.warning("Worker warm-up failed: %s", exc)


def ensure_http_worker(
    *,
    data_dir: Path,
    semantic: bool = False,
    allow_spawn: bool = True,
    log_dir: Optional[Path] = None,
) -> Optional[str]:
    """Ensure an HTTP worker is running, returning its endpoint."""

    provided = resolve_endpoint()
    if provided and _healthcheck(provided):
        return provided

    data_dir = data_dir.expanduser()
    data_dir.mkdir(parents=True, exist_ok=True)

    state_path = _default_state_path(data_dir)
    state = _read_state(state_path)
    if state:
        endpoint = state.get("endpoint")
        if endpoint and _healthcheck(endpoint):
            return endpoint

    if not allow_spawn:
        return state.get("endpoint") if state else None

    port = _find_free_port()
    endpoint = f"http://{DEFAULT_HOST}:{port}/mcp"
    log_dir = log_dir or data_dir
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / "worker.log"

    cmd = [
        sys.executable,
        "-m",
        "greeum.cli",
        "mcp",
        "serve",
        "-t",
        "http",
        "--host",
        DEFAULT_HOST,
        "--port",
        str(port),
    ]
    if semantic:
        cmd.append("--semantic")

    env = os.environ.copy()
    env.setdefault("GREEUM_DATA_DIR", str(data_dir))
    env.setdefault("GREEUM_QUIET", "true")

    creationflags = 0
    if os.name == "nt":  # pragma: no cover - windows only
        creationflags = getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0)

    with open(log_file, "a", encoding="utf-8") as log_handle:
        proc = subprocess.Popen(
            cmd,
            stdout=log_handle,
            stderr=subprocess.STDOUT,
            env=env,
            start_new_session=os.name != "nt",
            creationflags=creationflags,
        )

    # Wait for health check
    deadline = time.time() + START_TIMEOUT
    while time.time() < deadline:
        if _healthcheck(endpoint):
            _write_state(
                state_path,
                {
                    "endpoint": endpoint,
                    "pid": proc.pid,
                    "started_at": datetime.utcnow().isoformat() + "Z",
                    "semantic": bool(semantic),
                    "log": str(log_file),
                },
            )
            _warmup_worker(endpoint, semantic)
            return endpoint
        if proc.poll() is not None:
            break
        time.sleep(0.5)

    raise RuntimeError("Worker did not become healthy in time")


def get_worker_state(data_dir: Path) -> Optional[dict]:
    """Return the stored worker state for the given data directory, if available."""

    data_dir = Path(data_dir).expanduser()
    return _read_state(_default_state_path(data_dir))


__all__ = ["ensure_http_worker", "get_worker_state"]

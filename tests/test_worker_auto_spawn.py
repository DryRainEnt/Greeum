import json
import os
import signal
import subprocess
import sys
import time
import urllib.parse
from pathlib import Path

import pytest


@pytest.mark.slow
def test_cli_auto_spawns_worker(tmp_path):
    env = os.environ.copy()
    env.update(
        {
            "GREEUM_DATA_DIR": str(tmp_path),
            "GREEUM_DISABLE_ST": "1",
            "GREEUM_USE_WORKER": "1",
        }
    )

    add_cmd = [
        sys.executable,
        "-m",
        "greeum.cli",
        "memory",
        "add",
        "Auto spawned worker test",
        "--importance",
        "0.5",
    ]

    proc = subprocess.run(
        add_cmd,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=False,
    )

    assert proc.returncode == 0, f"CLI add failed: {proc.stdout}\n{proc.stderr}"
    assert "Memory Successfully Added" in proc.stdout, proc.stdout

    state_path = Path(tmp_path) / "worker_state.json"
    assert state_path.exists(), "Worker state file not created"

    state = json.loads(state_path.read_text(encoding="utf-8"))
    endpoint = state.get("endpoint")
    pid = state.get("pid")
    assert endpoint and endpoint.startswith("http"), state
    assert isinstance(pid, int)

    # Ensure worker is alive
    assert _health(endpoint), "Auto-spawned worker not healthy"

    # Kill worker to avoid leaking processes
    try:
        os.kill(pid, signal.SIGTERM)
    except AttributeError:  # Windows fallback
        subprocess.run(["taskkill", "/PID", str(pid), "/T", "/F"], check=False)


def _health(endpoint: str, timeout: float = 3.0) -> bool:
    import urllib.request

    parsed = urllib.parse.urlparse(endpoint)
    path = parsed.path or "/mcp"
    if path.endswith("/mcp"):
        path = path[: -len("/mcp")] + "/healthz"
    else:
        path = "/healthz"
    health_url = f"{parsed.scheme}://{parsed.netloc}{path}"
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            with urllib.request.urlopen(health_url, timeout=1.0) as response:
                return response.status == 200
        except Exception:
            time.sleep(0.2)
    return False

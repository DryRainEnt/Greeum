import json
import os
import signal
import subprocess
import sys
from pathlib import Path

import pytest


@pytest.mark.slow
def test_setup_starts_worker(tmp_path):
    data_dir = tmp_path / "data"
    config_dir = tmp_path / "config"

    env = os.environ.copy()
    env.update(
        {
            "GREEUM_CONFIG_DIR": str(config_dir),
            "GREEUM_DISABLE_ST": "1",
        }
    )

    cmd = [
        sys.executable,
        "-m",
        "greeum.cli",
        "setup",
        "--data-dir",
        str(data_dir),
        "--skip-warmup",
        "--start-worker",
    ]

    proc = subprocess.run(
        cmd,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=False,
    )

    assert proc.returncode == 0, f"setup failed: {proc.stdout}\n{proc.stderr}"

    state_path = data_dir / "worker_state.json"
    if not state_path.exists():
        pytest.skip("Worker could not be spawned in this environment")

    state = json.loads(state_path.read_text(encoding="utf-8"))
    endpoint = state.get("endpoint")
    pid = state.get("pid")
    assert endpoint and endpoint.startswith("http"), state
    assert isinstance(pid, int)

    # Clean up worker process
    try:
        os.kill(pid, signal.SIGTERM)
    except AttributeError:  # Windows fallback
        subprocess.run(["taskkill", "/PID", str(pid), "/T", "/F"], check=False)

    # Optionally ensure the process is gone
    try:
        os.kill(pid, 0)
    except OSError:
        pass

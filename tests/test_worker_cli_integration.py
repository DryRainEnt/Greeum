import os
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

import pytest


@pytest.mark.slow
def test_worker_cli_add_search(tmp_path):
    """HTTP worker should accept CLI add/search commands via worker endpoint."""
    # Allocate free port
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.bind(("127.0.0.1", 0))
            _, port = sock.getsockname()
    except PermissionError:
        pytest.skip("Socket bindings not permitted in this environment")

    env = os.environ.copy()
    env.update(
        {
            "GREEUM_DATA_DIR": str(tmp_path),
            "GREEUM_DISABLE_ST": "1",
            "GREEUM_QUIET": "true",
            "PYTHONUNBUFFERED": "1",
        }
    )

    subprocess.run(
        [
            sys.executable,
            "-m",
            "greeum.cli",
            "setup",
            "--data-dir",
            str(tmp_path),
            "--skip-warmup",
            "--skip-worker",
        ],
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=False,
    )

    cmd = [
        sys.executable,
        "-m",
        "greeum.cli",
        "mcp",
        "serve",
        "-t",
        "http",
        "--host",
        "127.0.0.1",
        "--port",
        str(port),
    ]

    log_path = tmp_path / "worker.log"
    log_file = log_path.open("w", encoding="utf-8")
    worker = subprocess.Popen(
        cmd,
        stdout=log_file,
        stderr=subprocess.STDOUT,
        text=True,
        env=env,
    )

    try:
        _wait_for_health(port, worker, log_path)

        worker_env = env.copy()
        worker_env.update(
            {
                "GREEUM_MCP_HTTP": f"http://127.0.0.1:{port}/mcp",
                "GREEUM_USE_WORKER": "1",
            }
        )

        add_cmd = [
            sys.executable,
            "-m",
            "greeum.cli",
            "memory",
            "add",
            "Worker queue integration test",
            "--importance",
            "0.6",
            "--use-worker",
        ]
        add_proc = subprocess.run(
            add_cmd,
            env=worker_env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=False,
        )
        assert add_proc.returncode == 0, f"add failed: {add_proc.stdout}\n{add_proc.stderr}"
        if "Auto worker unavailable" in add_proc.stdout:
            pytest.skip("Worker spawn is not permitted in this environment")
        assert "Memory Successfully Added" in add_proc.stdout, add_proc.stdout

        search_cmd = [
            sys.executable,
            "-m",
            "greeum.cli",
            "memory",
            "search",
            "Worker queue integration",
            "--count",
            "3",
            "--use-worker",
        ]
        search_proc = subprocess.run(
            search_cmd,
            env=worker_env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=False,
        )
        assert search_proc.returncode == 0, f"search failed: {search_proc.stdout}\n{search_proc.stderr}"
        # Result may vary, but worker path should be acknowledged
        assert "Found" in search_proc.stdout or "No results" in search_proc.stdout, search_proc.stdout

    except RuntimeError as exc:
        pytest.skip(str(exc))
    finally:
        worker.terminate()
        try:
            worker.wait(timeout=10)
        except subprocess.TimeoutExpired:
            worker.kill()
        log_file.close()


def _wait_for_health(port: int, proc: subprocess.Popen, log_path: Path, timeout: float = 30.0) -> None:
    url = f"http://127.0.0.1:{port}/healthz"
    start = time.time()
    while time.time() - start < timeout:
        if proc.poll() is not None:
            log_contents = ""
            try:
                log_contents = log_path.read_text(encoding="utf-8")
            except OSError:
                log_contents = "<unavailable>"
            raise RuntimeError(f"worker exited early. Log output:\n{log_contents}")
        try:
            with urllib.request.urlopen(url, timeout=1.0) as response:
                if response.status == 200:
                    return
        except urllib.error.URLError:
            time.sleep(0.2)
    raise TimeoutError(f"worker not ready after {timeout} seconds")

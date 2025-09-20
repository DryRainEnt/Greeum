"""Environment detection utilities for MCP adapter selection."""
from __future__ import annotations

import os
import platform
from dataclasses import dataclass
from typing import Dict, Mapping, Optional

_PROC_OSRELEASE = "/proc/sys/kernel/osrelease"
_PROC_VERSION = "/proc/version"


@dataclass(frozen=True)
class EnvironmentSnapshot:
    """Captures runtime environment signals used for MCP detection."""

    system: str
    release: str
    version: str
    os_name: str
    shell: str
    term_program: str
    prompt: str
    ps_module_path: str
    wsl_interop: str

    def to_debug_dict(self) -> Dict[str, str]:
        """Return a dictionary suitable for debug logging."""

        return {
            "system": self.system,
            "release": self.release,
            "version": self.version,
            "os_name": self.os_name,
            "shell": self.shell,
            "term_program": self.term_program,
            "prompt": self.prompt,
            "ps_module_path": self.ps_module_path,
            "wsl_interop": self.wsl_interop,
        }


def get_environment_snapshot(env: Optional[Mapping[str, str]] = None) -> EnvironmentSnapshot:
    """Collect the current environment in a test-friendly structure."""

    environ = env if env is not None else os.environ
    return EnvironmentSnapshot(
        system=platform.system(),
        release=platform.release(),
        version=platform.version(),
        os_name=os.name,
        shell=environ.get("SHELL", ""),
        term_program=environ.get("TERM_PROGRAM", ""),
        prompt=environ.get("PROMPT", ""),
        ps_module_path=environ.get("PSModulePath", ""),
        wsl_interop=environ.get("WSL_INTEROP", ""),
    )


def _read_file_lower(path: str) -> str:
    """Read a file and return its lowercase contents, tolerating errors."""

    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as handle:
            return handle.read().lower()
    except OSError:
        return ""


def _path_contains_microsoft(path: str) -> bool:
    """Check whether the given path contains the string 'microsoft'."""

    if not os.path.exists(path):
        return False
    return "microsoft" in _read_file_lower(path)


def is_wsl(snapshot: Optional[EnvironmentSnapshot] = None) -> bool:
    """Return True when the runtime is Windows Subsystem for Linux."""

    snap = snapshot or get_environment_snapshot()
    release = snap.release.lower()
    if "microsoft" in release:
        return True
    if snap.system != "Linux":
        return False
    if snap.wsl_interop:
        return True
    if _path_contains_microsoft(_PROC_OSRELEASE):
        return True
    if _path_contains_microsoft(_PROC_VERSION):
        return True
    return False


def is_powershell(snapshot: Optional[EnvironmentSnapshot] = None) -> bool:
    """Return True when running inside PowerShell on Windows."""

    snap = snapshot or get_environment_snapshot()
    if snap.system != "Windows" and snap.os_name != "nt":
        return False

    term_program = snap.term_program.lower()
    if term_program in {"powershell", "pwsh"}:
        return True

    shell = snap.shell.lower()
    if shell.endswith("powershell") or shell.endswith("powershell.exe"):
        return True
    if "powershell" in shell:
        return True

    prompt = snap.prompt.upper()
    if prompt.startswith("PS"):
        return True

    if "powershell" in snap.ps_module_path.lower():
        return True

    return False


def is_macos(snapshot: Optional[EnvironmentSnapshot] = None) -> bool:
    """Return True for macOS runtimes."""

    snap = snapshot or get_environment_snapshot()
    return snap.system == "Darwin"


def is_linux(snapshot: Optional[EnvironmentSnapshot] = None) -> bool:
    """Return True for conventional Linux environments (excluding WSL)."""

    snap = snapshot or get_environment_snapshot()
    return snap.system == "Linux" and not is_wsl(snap)


def detect_runtime(snapshot: Optional[EnvironmentSnapshot] = None) -> str:
    """Detect the current runtime label used for MCP adapter selection."""

    snap = snapshot or get_environment_snapshot()
    if is_wsl(snap):
        return "wsl"
    if is_powershell(snap):
        return "powershell"
    if is_macos(snap):
        return "macos"
    if is_linux(snap):
        return "linux"
    return "unknown"


_RUNTIME_TO_ADAPTER = {
    "wsl": "fastmcp",
    "powershell": "fastmcp",
    "macos": "jsonrpc",
    "linux": "jsonrpc",
}


def map_runtime_to_adapter(runtime: str) -> str:
    """Map the detected runtime to a named adapter."""

    return _RUNTIME_TO_ADAPTER.get(runtime, "jsonrpc")


def choose_adapter(snapshot: Optional[EnvironmentSnapshot] = None) -> Dict[str, str]:
    """Return runtime detection summary for adapter selection."""

    snap = snapshot or get_environment_snapshot()
    runtime = detect_runtime(snap)
    adapter = map_runtime_to_adapter(runtime)
    return {
        "runtime": runtime,
        "adapter": adapter,
        "details": snap.to_debug_dict(),
    }

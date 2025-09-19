import pytest

from greeum.mcp import environment_detector as envdet


def _snapshot(**overrides):
    defaults = {
        "system": "Linux",
        "release": "",
        "version": "",
        "os_name": "posix",
        "shell": "",
        "term_program": "",
        "prompt": "",
        "ps_module_path": "",
        "wsl_interop": "",
    }
    defaults.update(overrides)
    return envdet.EnvironmentSnapshot(**defaults)


def test_detect_runtime_wsl(monkeypatch):
    monkeypatch.setattr(envdet, "_path_contains_microsoft", lambda path: False)
    snapshot = _snapshot(system="Linux", release="5.15.90-microsoft-standard-WSL2")
    assert envdet.detect_runtime(snapshot) == "wsl"


def test_detect_runtime_wsl_by_env(monkeypatch):
    monkeypatch.setattr(envdet, "_path_contains_microsoft", lambda path: False)
    snapshot = _snapshot(system="Linux", release="5.15.90-generic", wsl_interop="/run/WSL/123")
    assert envdet.is_wsl(snapshot) is True


def test_detect_runtime_powershell(monkeypatch):
    snapshot = _snapshot(
        system="Windows",
        os_name="nt",
        shell="C:/Program Files/PowerShell/7/pwsh.exe",
        term_program="",
        prompt="PS C:/>",
    )
    assert envdet.detect_runtime(snapshot) == "powershell"


def test_detect_runtime_macos(monkeypatch):
    snapshot = _snapshot(system="Darwin", os_name="posix")
    assert envdet.detect_runtime(snapshot) == "macos"


def test_detect_runtime_linux(monkeypatch):
    monkeypatch.setattr(envdet, "_path_contains_microsoft", lambda path: False)
    snapshot = _snapshot(system="Linux", release="6.1.0-ubuntu")
    assert envdet.detect_runtime(snapshot) == "linux"


def test_detect_runtime_unknown(monkeypatch):
    snapshot = _snapshot(system="FreeBSD", os_name="posix")
    assert envdet.detect_runtime(snapshot) == "unknown"


def test_map_runtime_to_adapter():
    assert envdet.map_runtime_to_adapter("wsl") == "fastmcp"
    assert envdet.map_runtime_to_adapter("powershell") == "fastmcp"
    assert envdet.map_runtime_to_adapter("macos") == "jsonrpc"
    assert envdet.map_runtime_to_adapter("linux") == "jsonrpc"
    assert envdet.map_runtime_to_adapter("unknown") == "jsonrpc"


def test_choose_adapter_includes_details(monkeypatch):
    monkeypatch.setattr(envdet, "_path_contains_microsoft", lambda path: False)
    snapshot = _snapshot(system="Linux", release="6.1.0-ubuntu")
    result = envdet.choose_adapter(snapshot)
    assert result["runtime"] == "linux"
    assert result["adapter"] == "jsonrpc"
    assert result["details"]["system"] == "Linux"

import types
import sys
import logging
from pathlib import Path


def _prepare_dummy_module(name: str, version: str = "1.0"):
    module = types.ModuleType(name)
    module.__version__ = version
    return module


def _inject_dummy_mcp(monkeypatch):
    root_module = types.ModuleType("mcp")

    server_module = types.ModuleType("mcp.server")
    fastmcp_module = types.ModuleType("mcp.server.fastmcp")

    class DummyFastMCP:
        def __init__(self, *_, **__):
            pass

        def tool(self, *_, **__):
            def decorator(fn):
                return fn

            return decorator

        def resource(self, *_, **__):
            def decorator(fn):
                return fn

            return decorator

        def run(self, *_, **__):
            return None

    fastmcp_module.FastMCP = DummyFastMCP
    server_module.fastmcp = fastmcp_module
    root_module.server = server_module

    monkeypatch.setitem(sys.modules, "mcp", root_module)
    monkeypatch.setitem(sys.modules, "mcp.server", server_module)
    monkeypatch.setitem(sys.modules, "mcp.server.fastmcp", fastmcp_module)


def test_check_dependencies_outputs_ascii(monkeypatch, caplog):
    """check_dependencies 로그가 ASCII로 인코딩될 수 있는지 확인한다."""
    project_root = Path(__file__).resolve().parents[1]

    _inject_dummy_mcp(monkeypatch)

    # 패키지 스텁을 구성해 greeum.mcp.server를 로드할 수 있도록 한다.
    greeum_pkg = types.ModuleType("greeum")
    greeum_pkg.__path__ = [str(project_root / "greeum")]
    monkeypatch.setitem(sys.modules, "greeum", greeum_pkg)

    greeum_mcp_pkg = types.ModuleType("greeum.mcp")
    greeum_mcp_pkg.__path__ = [str(project_root / "greeum" / "mcp")]
    monkeypatch.setitem(sys.modules, "greeum.mcp", greeum_mcp_pkg)

    import importlib

    server = importlib.import_module("greeum.mcp.server")

    # 의존성 모듈을 더미로 주입해 검사 통과를 보장한다.
    monkeypatch.setitem(sys.modules, "fastapi", _prepare_dummy_module("fastapi", "1.0"))
    monkeypatch.setitem(sys.modules, "uvicorn", _prepare_dummy_module("uvicorn", "0.1"))

    # greeum.__version__이 없는 환경을 대비해 보장
    if not hasattr(greeum_pkg, "__version__"):
        monkeypatch.setattr(greeum_pkg, "__version__", "0.0-test", raising=False)

    caplog.set_level(logging.INFO, logger="greeummcp")

    assert server.check_dependencies() is True

    # check_dependencies가 남긴 모든 메시지가 ASCII로 인코딩 가능한지 확인한다.
    assert caplog.records, "로그 레코드가 생성되어야 한다"
    for record in caplog.records:
        message = record.getMessage()
        message.encode("ascii")

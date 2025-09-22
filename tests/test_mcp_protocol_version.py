import pytest

from greeum.mcp.native.protocol import (
    JSONRPCProcessor,
    DEFAULT_PROTOCOL_VERSION,
)


@pytest.mark.asyncio
async def test_initialize_echoes_supported_protocol_version():
    processor = JSONRPCProcessor(tool_handler=None)
    params = {
        "protocolVersion": "1.0",
        "capabilities": {},
        "clientInfo": {"name": "codex-cli", "version": "0.3.2"},
    }

    result = await processor._handle_initialize(params)

    assert result["protocolVersion"] == "1.0"


@pytest.mark.asyncio
async def test_initialize_falls_back_for_unknown_protocol_version():
    processor = JSONRPCProcessor(tool_handler=None)
    params = {
        "protocolVersion": "codex-alpha",
        "capabilities": {},
        "clientInfo": {"name": "codex-cli", "version": "0.3.2"},
    }

    result = await processor._handle_initialize(params)

    assert result["protocolVersion"] == DEFAULT_PROTOCOL_VERSION

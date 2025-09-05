#!/bin/bash
# Greeum v2.0 Simple MCP Bridge Launcher

# Python path auto-detection
PYTHON_CMD=""
if command -v python3 &> /dev/null; then
    PYTHON_CMD="python3"
elif command -v python &> /dev/null; then
    PYTHON_CMD="python"
else
    echo "Error: Python not found" >&2
    exit 1
fi

# Script directory and server execution
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SERVER_SCRIPT="${SCRIPT_DIR}/greeum/mcp/simple_mcp_bridge.py"

if [ ! -f "$SERVER_SCRIPT" ]; then
    echo "Error: Simple MCP bridge not found at $SERVER_SCRIPT" >&2
    exit 1
fi

# Set Python path and run server
export PYTHONPATH="${SCRIPT_DIR}:${PYTHONPATH}"
cd "$SCRIPT_DIR"
exec "$PYTHON_CMD" "$SERVER_SCRIPT"
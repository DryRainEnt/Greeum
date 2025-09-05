#!/bin/bash
# Greeum v2.0 Universal MCP Server Launcher
# 환경 독립적 실행 스크립트

# Python 경로 자동 감지
PYTHON_CMD=""
if command -v python3 &> /dev/null; then
    PYTHON_CMD="python3"
elif command -v python &> /dev/null; then
    PYTHON_CMD="python"
else
    echo "Error: Python not found" >&2
    exit 1
fi

# 스크립트 디렉토리 기준으로 서버 실행
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SERVER_SCRIPT="${SCRIPT_DIR}/greeum/mcp/universal_mcp_server.py"

if [ ! -f "$SERVER_SCRIPT" ]; then
    echo "Error: Universal MCP server not found at $SERVER_SCRIPT" >&2
    exit 1
fi

# 서버 실행
exec "$PYTHON_CMD" "$SERVER_SCRIPT"
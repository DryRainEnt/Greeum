"""
GreeumMCP - Greeum Memory Engine as MCP Server
Native MCP Server 우선 로딩
"""

__version__ = "2.3.0a4"

# Native MCP Server 우선 노출 (FastMCP 의존성 제거)
try:
    from .native import run_server_sync, run_native_mcp_server, GreeumNativeMCPServer
    # Native MCP Server를 기본으로 설정
    __all__ = ["run_server_sync", "run_native_mcp_server", "GreeumNativeMCPServer"]
except ImportError as e:
    # Native MCP Server 실패 시에만 Legacy 서버 시도
    try:
        from .server import GreeumMCPServer
        __all__ = ["GreeumMCPServer"]
    except ImportError:
        # 모든 서버 실패 시 빈 패키지
        __all__ = []

# Convenience function - Native MCP Server 사용
def run_server(data_dir="./data", server_name="greeum_mcp", port=8000, transport="stdio", greeum_config=None):
    """
    Create and run a Native Greeum MCP server.
    
    Args:
        data_dir: Directory to store memory data (환경변수 GREEUM_DATA_DIR로 오버라이드 가능)
        server_name: Name of the MCP server
        port: Port for HTTP transport (현재 stdio만 지원)
        transport: Transport type (현재 'stdio'만 지원)
        greeum_config: Additional configuration (미사용)
    """
    import os
    import logging
    
    # 환경변수 설정
    if data_dir != "./data":
        os.environ['GREEUM_DATA_DIR'] = data_dir
    
    # Native MCP Server 실행 (FastMCP 완전 배제)
    try:
        run_server_sync()
    except NameError:
        # Native 서버가 import되지 않은 경우 에러 메시지
        logging.error("❌ Native MCP Server not available. Please install: pip install anyio>=4.5")
        raise RuntimeError("Native MCP Server dependencies not installed") 
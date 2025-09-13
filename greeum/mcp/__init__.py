"""
GreeumMCP - Greeum Memory Engine as MCP Server
Native MCP Server 우선 로딩
"""

# Use main package version
try:
    from greeum import __version__
except ImportError:
    __version__ = "unknown"

# Working MCP Server를 기본으로 복원 (긴급 수정)
try:
    from .working_mcp_server import WorkingGreeumMCPServer
    # Working MCP Server를 기본으로 설정
    __all__ = ["WorkingGreeumMCPServer"]
except ImportError as e:
    # Working MCP Server 실패 시에만 Native 서버 시도
    try:
        from .native import run_server_sync, run_native_mcp_server, GreeumNativeMCPServer
        __all__ = ["run_server_sync", "run_native_mcp_server", "GreeumNativeMCPServer"]
    except ImportError:
        # 모든 서버 실패 시 빈 패키지
        __all__ = []

# Convenience function - Working MCP Server 사용 (복원)
def run_server(data_dir="./data", server_name="greeum_mcp", port=8000, transport="stdio", greeum_config=None):
    """
    Create and run a Working Greeum MCP server.
    
    Args:
        data_dir: Directory to store memory data (환경변수 GREEUM_DATA_DIR로 오버라이드 가능)
        server_name: Name of the MCP server  
        port: Port for HTTP transport (현재 stdio만 지원)
        transport: Transport type (현재 'stdio'만 지원)
        greeum_config: Additional configuration (미사용)
    """
    import os
    import logging
    import asyncio
    
    # 환경변수 설정
    if data_dir != "./data":
        os.environ['GREEUM_DATA_DIR'] = data_dir
    
    # Working MCP Server 실행
    try:
        from .working_mcp_server import main
        asyncio.run(main())
    except ImportError as e:
        logging.error(f"[ERROR] Working MCP Server not available: {e}")
        raise RuntimeError("Working MCP Server dependencies not installed") 
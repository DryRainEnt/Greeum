#!/usr/bin/env python3
"""
Greeum Native MCP Server Package
FastMCP 없는 순수 네이티브 MCP 서버 구현

Public API:
- GreeumNativeMCPServer: 메인 서버 클래스
- run_native_mcp_server: 비동기 서버 실행 함수  
- run_server_sync: 동기 래퍼 함수 (CLI 진입점)

특징:
- anyio 기반 안전한 AsyncIO 처리
- Windows 호환성 보장
- 기존 Greeum 로직 100% 재사용
- JSON-RPC 2.0 + MCP 프로토콜 완전 준수
"""

# Use main package version
try:
    from greeum import __version__
except ImportError:
    __version__ = "unknown"
__author__ = "DryRainEnt"

# 메인 서버 클래스 및 실행 함수 노출
try:
    from .server import GreeumNativeMCPServer, run_native_mcp_server, run_server_sync
    
    __all__ = [
        "GreeumNativeMCPServer",
        "run_native_mcp_server", 
        "run_server_sync"
    ]
    
except ImportError as e:
    # 의존성 누락 시 경고만 출력 (전체 패키지 중단 방지)
    import sys
    print(f"Warning: Native MCP server unavailable: {e}", file=sys.stderr)
    
    __all__ = []
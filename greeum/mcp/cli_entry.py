#!/usr/bin/env python3
"""
Greeum MCP CLI Entry Point
완전히 분리된 CLI 전용 MCP 서버 진입점

🎯 설계 원칙:
- CLI와 서버 로직 완전 분리
- AsyncIO 중첩 호출 문제 근본 해결
- 단일 책임 원칙 (SRP) 준수
- 향후 확장성 (WebSocket, HTTP 등) 고려

🔧 아키텍처:
- cli_entry.py: CLI 호출 전용 진입점
- server_core.py: 순수 서버 로직
- transport별 어댑터 분리 가능
"""

import asyncio
import logging
import sys
import os
from typing import Optional

# 로깅 설정 (stderr로만)
logging.basicConfig(level=logging.INFO, stream=sys.stderr, format='%(levelname)s:%(name)s:%(message)s')
logger = logging.getLogger("greeum_mcp_cli")

async def serve_stdio() -> None:
    """STDIO transport로 MCP 서버 시작"""
    try:
        # 서버 코어 로직 import (지연 import로 의존성 격리)
        from .server_core import GreeumMCPServer
        
        # 서버 인스턴스 생성 및 시작
        server = GreeumMCPServer()
        await server.initialize()
        
        logger.info("🚀 Starting Greeum MCP server (STDIO transport)")
        await server.run_stdio()
        
    except ImportError as e:
        logger.error(f"[ERROR] Failed to import server core: {e}")
        raise RuntimeError(f"MCP server dependencies not available: {e}")
    except Exception as e:
        logger.error(f"[ERROR] MCP server failed to start: {e}")
        raise

async def serve_websocket(port: int = 3000) -> None:
    """WebSocket transport로 MCP 서버 시작 (향후 확장)"""
    logger.info(f"🚀 Starting Greeum MCP server (WebSocket transport on port {port})")
    # WebSocket 구현은 향후 확장
    raise NotImplementedError("WebSocket transport not implemented yet")

def run_cli_server(transport: str = "stdio", port: int = 3000) -> None:
    """
    CLI에서 호출되는 메인 진입점
    
    Args:
        transport: 전송 방식 ("stdio" 또는 "websocket")
        port: WebSocket 포트 (WebSocket 사용시)
    """
    try:
        if transport == "stdio":
            # 새 이벤트 루프에서 STDIO 서버 실행
            asyncio.run(serve_stdio())
        elif transport == "websocket":
            # 새 이벤트 루프에서 WebSocket 서버 실행
            asyncio.run(serve_websocket(port))
        else:
            raise ValueError(f"Unsupported transport: {transport}")
            
    except KeyboardInterrupt:
        logger.info("👋 MCP server stopped by user")
    except Exception as e:
        logger.error(f"[ERROR] MCP server error: {e}")
        sys.exit(1)

# 직접 실행 방지 (CLI 전용)
if __name__ == "__main__":
    logger.error("[ERROR] This module is for CLI use only. Use 'greeum mcp serve' command.")
    sys.exit(1)
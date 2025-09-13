#!/usr/bin/env python3
"""
Greeum Native MCP Server - Main Server Class
FastMCP 없는 순수 네이티브 MCP 서버 구현

핵심 기능:
- anyio 기반 안전한 AsyncIO 처리 (asyncio.run() 중첩 방지)
- 완전한 Greeum 컴포넌트 초기화
- STDIO 전송 계층과 JSON-RPC 프로토콜 통합
- 기존 비즈니스 로직 100% 재사용
- Claude Desktop 호환성을 위한 로그 출력 억제 지원
"""

import logging
import sys
import os
from typing import Optional, Dict, Any

# anyio 의존성 확인
try:
    import anyio
except ImportError:
    print("ERROR: anyio is required. Install with: pip install anyio>=4.5", file=sys.stderr)
    sys.exit(1)

# Greeum core imports
try:
    from greeum.core.block_manager import BlockManager
    from greeum.core import DatabaseManager  # Thread-safe factory pattern  
    from greeum.core.stm_manager import STMManager
    from greeum.core.duplicate_detector import DuplicateDetector
    from greeum.core.quality_validator import QualityValidator
    from greeum.core.usage_analytics import UsageAnalytics
    GREEUM_AVAILABLE = True
except ImportError as e:
    print(f"ERROR: Greeum core components not available: {e}", file=sys.stderr)
    GREEUM_AVAILABLE = False

from .transport import STDIOServer
from .protocol import JSONRPCProcessor
from .tools import GreeumMCPTools
from .types import SessionMessage

# GREEUM_QUIET 환경변수 확인
QUIET_MODE = os.getenv('GREEUM_QUIET', '').lower() in ('true', '1', 'yes')

# 로깅 설정 (stderr 전용 - STDOUT 오염 방지)
# quiet 모드에서는 로깅 레벨을 WARNING 이상으로 설정하여 INFO 로그 억제
log_level = logging.WARNING if QUIET_MODE else logging.INFO
logging.basicConfig(
    level=log_level, 
    stream=sys.stderr, 
    format='%(levelname)s:%(name)s:%(message)s'
)
logger = logging.getLogger("greeum_native_server")

class GreeumNativeMCPServer:
    """
    Greeum Native MCP Server
    
    특징:
    - FastMCP 완전 배제로 AsyncIO 충돌 근본 해결
    - anyio + Pydantic 기반 안전한 구현
    - 기존 Greeum 비즈니스 로직 100% 재사용
    - Windows 호환성 보장
    """
    
    def __init__(self):
        self.greeum_components: Optional[Dict[str, Any]] = None
        self.tools_handler: Optional[GreeumMCPTools] = None
        self.protocol_processor: Optional[JSONRPCProcessor] = None
        self.initialized = False
        
        logger.info("Greeum Native MCP Server created")
    
    async def initialize(self) -> None:
        """
        서버 컴포넌트 초기화
        
        초기화 순서:
        1. Greeum 컴포넌트 초기화
        2. MCP 도구 핸들러 생성
        3. JSON-RPC 프로토콜 프로세서 생성
        """
        if self.initialized:
            return
            
        if not GREEUM_AVAILABLE:
            raise RuntimeError("ERROR: Greeum core components not available")
        
        try:
            # Greeum 컴포넌트 초기화 (기존 패턴과 동일)
            logger.info("Initializing Greeum components...")
            
            db_manager = DatabaseManager()
            block_manager = BlockManager(db_manager)
            stm_manager = STMManager(db_manager)
            duplicate_detector = DuplicateDetector(db_manager)
            quality_validator = QualityValidator()
            usage_analytics = UsageAnalytics(db_manager)
            
            self.greeum_components = {
                'db_manager': db_manager,
                'block_manager': block_manager,
                'stm_manager': stm_manager,
                'duplicate_detector': duplicate_detector,
                'quality_validator': quality_validator,
                'usage_analytics': usage_analytics
            }
            
            logger.info("Greeum components initialized successfully")
            
            # MCP 도구 핸들러 초기화
            self.tools_handler = GreeumMCPTools(self.greeum_components)
            
            # JSON-RPC 프로토콜 프로세서 초기화
            self.protocol_processor = JSONRPCProcessor(self.tools_handler)
            
            self.initialized = True
            logger.info("Native MCP server initialization completed")
            
        except Exception as e:
            logger.error(f"Failed to initialize server: {e}")
            raise RuntimeError(f"Server initialization failed: {e}")
    
    async def run_stdio(self) -> None:
        """
        STDIO transport로 서버 실행
        
        anyio 기반 안전한 AsyncIO 처리:
        - asyncio.run() 사용 안 함 (충돌 방지)
        - anyio.create_task_group으로 동시 실행
        - Memory Object Streams로 메시지 전달
        """
        if not self.initialized:
            await self.initialize()
        
        logger.info("Starting Native MCP server with STDIO transport")
        
        try:
            # STDIO 서버 실행 (anyio 기반)
            stdio_server = STDIOServer(self._handle_message)
            await stdio_server.run()
            
        except KeyboardInterrupt:
            logger.info("Server stopped by user")
        except Exception as e:
            logger.error(f"Server error: {e}")
            raise
    
    async def _handle_message(self, session_message: SessionMessage) -> Optional[SessionMessage]:
        """
        메시지 처리 핸들러
        
        Args:
            session_message: 수신된 세션 메시지
            
        Returns:
            Optional[SessionMessage]: 응답 메시지 (알림의 경우 None)
        """
        try:
            # JSON-RPC 프로토콜 프로세서에 위임
            response = await self.protocol_processor.process_message(session_message)
            return response
            
        except Exception as e:
            logger.error(f"Message handling error: {e}")
            
            # 에러 응답 생성 (가능한 경우)
            if hasattr(session_message.message, 'id'):
                from .types import JSONRPCError, JSONRPCErrorResponse, ErrorCodes
                
                error = JSONRPCError(
                    code=ErrorCodes.INTERNAL_ERROR,
                    message="Internal server error"
                )
                error_response = JSONRPCErrorResponse(
                    id=session_message.message.id,
                    error=error
                )
                return SessionMessage(message=error_response)
            
            return None
    
    async def shutdown(self) -> None:
        """서버 종료 처리"""
        try:
            if self.greeum_components:
                # 필요한 경우 컴포넌트 정리
                pass
            
            logger.info("Server shutdown completed")
        except Exception as e:
            logger.error(f"Error during shutdown: {e}")

# =============================================================================
# CLI 진입점 함수
# =============================================================================

async def run_native_mcp_server() -> None:
    """
    Native MCP 서버 실행 함수 (CLI에서 호출)
    
    anyio 기반으로 asyncio.run() 충돌 완전 회피
    """
    server = GreeumNativeMCPServer()
    
    try:
        await server.run_stdio()
    finally:
        await server.shutdown()

def run_server_sync(log_level: str = 'quiet') -> None:
    """
    동기 래퍼 함수 (CLI에서 직접 호출 가능)
    
    Args:
        log_level: 로깅 레벨 ('quiet', 'verbose', 'debug')
                  - quiet: WARNING 이상만 출력 (기본값)
                  - verbose: INFO 이상 출력
                  - debug: DEBUG 이상 모든 로그 출력
    
    anyio.run() 사용으로 안전한 실행
    """
    # 로깅 레벨 설정
    global QUIET_MODE
    
    if log_level == 'debug':
        target_level = logging.DEBUG
        is_quiet = False
    elif log_level == 'verbose':
        target_level = logging.INFO
        is_quiet = False
    else:  # 'quiet' 또는 기타
        target_level = logging.WARNING
        is_quiet = True
    
    # GREEUM_QUIET 환경변수가 있으면 무조건 quiet 모드
    if QUIET_MODE:
        target_level = logging.WARNING
        is_quiet = True
    
    # 로깅 레벨 적용
    logging.getLogger().setLevel(target_level)
    logger.setLevel(target_level)
    
    try:
        # anyio.run() 사용 - asyncio.run() 대신
        anyio.run(run_native_mcp_server)
    except KeyboardInterrupt:
        if not is_quiet:
            logger.info("Server stopped by user")
    except anyio.exceptions.CancelledError:
        # anyio TaskGroup이 KeyboardInterrupt를 CancelledError로 변환함
        if not is_quiet:
            logger.info("Server stopped by user")
    except Exception as e:
        # 오류는 quiet 모드에서도 출력 (WARNING 레벨)
        logger.error(f"[ERROR] Server startup error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    # 직접 실행 방지 (CLI 전용)
    logger.error("[ERROR] This module is for CLI use only. Use 'greeum mcp serve' command.")
    sys.exit(1)
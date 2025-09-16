#!/usr/bin/env python3
"""
Greeum Native MCP Server - Main Server Class
Pure native MCP server implementation without FastMCP

Core Features:
- Safe AsyncIO handling based on anyio (prevents asyncio.run() nesting)
- Complete Greeum component initialization
- STDIO transport layer and JSON-RPC protocol integration
- 100% business logic reuse
- Log output suppression support for Claude Desktop compatibility
"""

import logging
import sys
import os
import signal
import atexit
from typing import Optional, Dict, Any

# Check anyio dependency
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

# Check GREEUM_QUIET environment variable
QUIET_MODE = os.getenv('GREEUM_QUIET', '').lower() in ('true', '1', 'yes')

# Configure logging (stderr only - prevent STDOUT pollution)
# In quiet mode, set logging level to WARNING or higher to suppress INFO logs
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

            # Start model pre-warming in background (non-blocking)
            self._start_model_prewarming()

        except Exception as e:
            logger.error(f"Failed to initialize server: {e}")
            raise RuntimeError(f"Server initialization failed: {e}")

    def _start_model_prewarming(self):
        """
        백그라운드에서 모델 pre-warming 시작

        이 함수는 non-blocking으로 실행되어 서버 시작을 지연시키지 않음.
        첫 번째 메모리 저장이나 검색 요청 시 모델이 이미 로드되어 있어
        타임아웃을 방지함.
        """
        import threading

        def prewarm_model():
            try:
                logger.info("Starting model pre-warming in background...")
                from greeum.embedding_models import get_embedding

                # 더미 텍스트로 모델 초기화 트리거
                _ = get_embedding("Model pre-warming test")
                logger.info("✅ Model pre-warming completed successfully")
            except Exception as e:
                logger.warning(f"Model pre-warming failed (non-critical): {e}")

        # 별도 스레드에서 실행하여 서버 시작을 차단하지 않음
        prewarm_thread = threading.Thread(target=prewarm_model, daemon=True)
        prewarm_thread.start()
        logger.debug("Model pre-warming thread started")
    
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
                # Close database connections
                if 'db_manager' in self.greeum_components:
                    try:
                        db_manager = self.greeum_components['db_manager']
                        if hasattr(db_manager, 'conn'):
                            db_manager.conn.close()
                            logger.debug("Database connection closed")
                    except Exception as e:
                        logger.debug(f"Error closing database: {e}")

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

def cleanup_handler(signum=None, frame=None):
    """
    Clean up resources on exit
    """
    logger.info("Cleaning up MCP server resources...")
    try:
        # Close database connections if any
        import gc
        gc.collect()
    except Exception as e:
        logger.debug(f"Cleanup error: {e}")
    finally:
        if signum:
            sys.exit(0)

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
    # Register cleanup handlers
    signal.signal(signal.SIGTERM, cleanup_handler)
    signal.signal(signal.SIGINT, cleanup_handler)
    signal.signal(signal.SIGHUP, cleanup_handler)
    atexit.register(cleanup_handler)
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
    except anyio.CancelledError:
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
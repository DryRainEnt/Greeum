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
import asyncio
from typing import Optional, Dict, Any, Union, List, Tuple

import anyio

# Check anyio dependency
try:
    import anyio
except ImportError:
    print("ERROR: anyio is required. Install with: pip install anyio>=4.5", file=sys.stderr)
    sys.exit(1)

from .compat import CancelledError

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
        self._write_send_stream = None
        self._write_receive_stream = None
        self._write_worker_running = False
        
        logger.info("Greeum Native MCP Server created")
    
    async def initialize(self) -> None:
        """
        서버 컴포넌트 초기화

        초기화 순서:
        1. 기존 좀비 프로세스 정리 (v3.1.1rc2.dev8)
        2. Greeum 컴포넌트 초기화
        3. MCP 도구 핸들러 생성
        4. JSON-RPC 프로토콜 프로세서 생성
        """
        if self.initialized:
            return

        if not GREEUM_AVAILABLE:
            raise RuntimeError("ERROR: Greeum core components not available")

        # v3.1.1rc2.dev8: Clean up orphaned MCP processes before starting
        self._cleanup_orphaned_processes()
        
        try:
            # Greeum 컴포넌트 초기화 (기존 패턴과 동일)
            logger.info("Initializing Greeum components...")
            
            db_manager = DatabaseManager()
            block_manager = BlockManager(db_manager)
            stm_manager = STMManager(db_manager)
            duplicate_detector = DuplicateDetector(db_manager)
            quality_validator = QualityValidator()
            usage_analytics = UsageAnalytics(db_manager)

            # v3.1.1rc2.dev9: Initialize DFS search for smart routing
            from greeum.core.dfs_search import DFSSearchEngine
            dfs_search = DFSSearchEngine(db_manager)

            self.greeum_components = {
                'db_manager': db_manager,
                'block_manager': block_manager,
                'stm_manager': stm_manager,
                'duplicate_detector': duplicate_detector,
                'quality_validator': quality_validator,
                'usage_analytics': usage_analytics,
                'dfs_search': dfs_search  # v3.1.1rc2.dev9: Add for smart routing
            }
            
            logger.info("Greeum components initialized successfully")
            
            # MCP 도구 핸들러 초기화
            self.tools_handler = GreeumMCPTools(self.greeum_components)

            # JSON-RPC 프로토콜 프로세서 초기화
            self.protocol_processor = JSONRPCProcessor(self.tools_handler)

            self.initialized = True
            self.model_ready = False  # v3.1.1rc2.dev9: Track model loading status
            logger.info("Native MCP server initialization completed")

            # Initialize write queue (FIFO) for serializing add_memory requests
            try:
                send_stream, receive_stream = anyio.create_memory_object_stream(0)
                self._write_send_stream = send_stream
                self._write_receive_stream = receive_stream
            except Exception as queue_error:
                logger.warning(f"Failed to create write queue: {queue_error}")
                self._write_send_stream = None
                self._write_receive_stream = None

            # v3.1.1rc2.dev9: Start model loading AFTER connection established
            # This prevents connection timeout while still pre-loading the model
            try:
                # Check if event loop is running
                loop = asyncio.get_running_loop()
                loop.create_task(self._async_model_loading())
            except RuntimeError:
                # No running event loop, skip background loading
                logger.debug("No event loop available for background model loading")

        except Exception as e:
            logger.error(f"Failed to initialize server: {e}")
            raise RuntimeError(f"Server initialization failed: {e}")

    def _cleanup_orphaned_processes(self):
        """
        v3.1.1rc2.dev8: 기존 orphaned Greeum MCP 프로세스 정리

        판별 기준:
        1. 같은 명령어 패턴 (greeum mcp serve)
        2. PPID=1 (orphaned process)
        3. stdin/stdout/stderr가 연결 끊김
        4. 현재 프로세스보다 오래됨
        """
        try:
            import psutil
            current_pid = os.getpid()
            current_process = psutil.Process(current_pid)
            current_cmdline = ' '.join(current_process.cmdline())

            # greeum mcp serve 명령을 실행 중인 프로세스만 찾기
            if 'greeum' not in current_cmdline or 'mcp' not in current_cmdline:
                return  # Not an MCP server process, skip cleanup

            cleaned = 0
            for proc in psutil.process_iter(['pid', 'ppid', 'cmdline', 'create_time']):
                try:
                    # Skip current process
                    if proc.pid == current_pid:
                        continue

                    # Check if it's a Greeum MCP process
                    cmdline = ' '.join(proc.cmdline() or [])
                    if 'greeum' in cmdline and 'mcp' in cmdline and 'serve' in cmdline:
                        # Check if orphaned (PPID=1 on Unix/Linux/Mac)
                        if proc.ppid() == 1:
                            # Check if older than current process
                            if proc.create_time() < current_process.create_time():
                                logger.info(f"Terminating orphaned MCP process: PID={proc.pid}, age={current_process.create_time() - proc.create_time():.0f}s")
                                proc.terminate()
                                cleaned += 1
                                # Wait a bit for graceful termination
                                try:
                                    proc.wait(timeout=1.0)
                                except psutil.TimeoutExpired:
                                    # Force kill if not terminated
                                    logger.warning(f"Force killing stubborn process: PID={proc.pid}")
                                    proc.kill()
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue

            if cleaned > 0:
                logger.info(f"Cleaned up {cleaned} orphaned MCP processes")

        except ImportError:
            logger.debug("psutil not available, skipping orphan cleanup")
        except Exception as e:
            logger.warning(f"Failed to cleanup orphaned processes: {e}")

    async def _async_model_loading(self):
        """
        v3.1.1rc2.dev9: 비동기 모델 로딩

        연결이 완료된 후 백그라운드에서 모델을 로드합니다.
        이렇게 하면 초기 연결은 즉시 성공하고, 모델은 천천히 로드됩니다.
        """
        try:
            logger.info("Starting async model loading in background...")

            # asyncio 환경에서 별도 스레드로 동기 작업 실행
            import asyncio
            from greeum.embedding_models import get_embedding

            # Run synchronous model loading in executor
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None,  # Default executor (ThreadPoolExecutor)
                lambda: get_embedding("Model initialization test")
            )

            self.model_ready = True
            logger.info("✅ Model loading completed successfully")

        except Exception as e:
            logger.error(f"Model loading failed: {e}")
            # Model loading failure is not critical for basic operations
            # Some features may be degraded but server continues
            self.model_ready = False

    async def wait_for_model(self, timeout: float = 30.0):
        """
        v3.1.1rc2.dev9: 모델 로딩 대기

        모델이 필요한 작업 전에 호출하여 모델 로딩을 대기합니다.
        """
        start_time = asyncio.get_event_loop().time()
        while not self.model_ready:
            if asyncio.get_event_loop().time() - start_time > timeout:
                raise TimeoutError("Model loading timeout")
            await asyncio.sleep(0.1)
        return True

    async def _write_worker(self) -> None:
        """Serialize add_memory requests using a background worker."""

        if self._write_receive_stream is None:
            logger.debug("Write queue not available; worker exiting")
            return

        self._write_worker_running = True
        logger.info("Write worker started")

        try:
            async with self._write_receive_stream:
                async for job in self._write_receive_stream:
                    reply_stream = job.get("reply")
                    tool_name = job.get("name")
                    arguments = job.get("arguments", {})
                    result_text = ""

                    try:
                        if not hasattr(self.tools_handler, "execute_tool_internal"):
                            raise RuntimeError("Tool handler does not support internal execution")

                        result_text = await self.tools_handler.execute_tool_internal(tool_name, arguments)
                    except Exception as worker_err:
                        logger.error(f"Write worker failed to execute {tool_name}: {worker_err}")
                        result_text = f"ERROR: Failed to add memory: {worker_err}"

                    if reply_stream:
                        try:
                            await reply_stream.send(result_text)
                        finally:
                            await reply_stream.aclose()

        except Exception as worker_exception:
            logger.error(f"Write worker encountered an error: {worker_exception}")
        finally:
            self._write_worker_running = False
            logger.info("Write worker stopped")
    
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
            stdio_server = STDIOServer(self._handle_message)
            async with anyio.create_task_group() as tg:
                if self._write_receive_stream is not None:
                    if hasattr(self.tools_handler, "enable_write_queue"):
                        self.tools_handler.enable_write_queue(self._write_send_stream)
                    tg.start_soon(self._write_worker)
                tg.start_soon(stdio_server.run)

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

    async def handle_jsonrpc(self, payload: Union[Dict[str, Any], List[Dict[str, Any]]]) -> Union[Dict[str, Any], List[Dict[str, Any]], None]:
        """HTTP/WS 전송을 위한 JSON-RPC 메시지 처리"""

        if not self.initialized:
            await self.initialize()

        async def _process_single(message_dict: Dict[str, Any]) -> Optional[Dict[str, Any]]:
            session_message = SessionMessage.from_dict(message_dict)
            response_message = await self._handle_message(session_message)
            if response_message is None:
                return None
            return response_message.to_dict()

        # JSON-RPC batch 처리 지원
        if isinstance(payload, list):
            responses: List[Dict[str, Any]] = []
            for item in payload:
                response = await _process_single(item)
                if response is not None:
                    responses.append(response)
            return responses

        return await _process_single(payload)

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
    # Register cleanup handlers (guard unsupported signals for cross-platform compatibility)
    for _sig_name in ("SIGTERM", "SIGINT", "SIGHUP"):
        if hasattr(signal, _sig_name):
            signal.signal(getattr(signal, _sig_name), cleanup_handler)
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
    except CancelledError:
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

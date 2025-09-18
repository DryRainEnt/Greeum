#!/usr/bin/env python3
"""
Greeum Native MCP Server - STDIO Transport Layer
공식 Anthropic MCP Python SDK 패턴 기반 STDIO 전송 계층

핵심 기능:
- anyio 기반 크로스플랫폼 async I/O
- Windows UTF-8 인코딩 문제 해결
- Memory Object Streams으로 읽기/쓰기 분리
- JSON-RPC 메시지 라인 단위 처리
"""

import sys
import logging
from typing import AsyncGenerator, Optional, TYPE_CHECKING, Any
from io import TextIOWrapper

try:
    import anyio
except ImportError:
    raise ImportError("anyio is required. Install with: pip install anyio>=4.5")

from .compat import CancelledError, EndOfStream

if TYPE_CHECKING:  # pragma: no cover - type hints only
    from anyio.streams.memory import MemoryObjectSendStream, MemoryObjectReceiveStream
else:  # 런타임 호환성을 위해 지연 로딩
    MemoryObjectSendStream = Any  # type: ignore
    MemoryObjectReceiveStream = Any  # type: ignore

from .types import SessionMessage

# 로깅 설정 (stderr 전용 - STDOUT 오염 방지)
logger = logging.getLogger("greeum_native_transport")

class STDIOTransport:
    """
    STDIO 기반 MCP 전송 계층
    
    공식 패턴:
    - anyio.wrap_file로 플랫폼별 스트림 처리
    - TextIOWrapper + UTF-8로 Windows 호환성
    - Memory Object Streams로 비동기 메시지 큐
    """
    
    def __init__(self):
        self.read_stream: Optional[MemoryObjectReceiveStream] = None
        self.write_stream: Optional[MemoryObjectSendStream] = None
        self._read_stream_writer: Optional[MemoryObjectSendStream] = None
        self._write_stream_reader: Optional[MemoryObjectReceiveStream] = None
        
    @staticmethod
    def create_stdio_streams():
        """
        크로스플랫폼 STDIO 스트림 생성
        
        Windows 호환성:
        - TextIOWrapper + UTF-8 인코딩으로 플랫폼별 문제 해결
        - anyio.wrap_file로 비동기 래핑
        """
        # 공식 패턴: Windows 인코딩 문제 해결
        stdin = anyio.wrap_file(
            TextIOWrapper(sys.stdin.buffer, encoding="utf-8")
        )
        stdout = anyio.wrap_file(
            TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
        )
        
        return stdin, stdout
    
    async def initialize_streams(self):
        """메모리 객체 스트림 초기화"""
        # 읽기 스트림 (stdin → message processor)
        self._read_stream_writer, self.read_stream = anyio.create_memory_object_stream()
        
        # 쓰기 스트림 (message processor → stdout)  
        self.write_stream, self._write_stream_reader = anyio.create_memory_object_stream()
        
        logger.info("Memory object streams initialized")
    
    async def stdin_reader(self) -> None:
        """
        STDIN에서 JSON-RPC 메시지 읽기
        
        처리 과정:
        1. STDIN에서 라인 단위 읽기
        2. SessionMessage로 파싱
        3. 읽기 스트림에 전송
        """
        stdin, _ = self.create_stdio_streams()
        
        try:
            async for line in stdin:
                line = line.strip()
                if not line:
                    continue
                    
                try:
                    # JSON-RPC 메시지 파싱
                    session_message = SessionMessage.from_json(line)
                    await self._read_stream_writer.send(session_message)
                    logger.debug(f"Received message: {session_message.message.model_dump().get('method', 'response')}")
                    
                except Exception as e:
                    logger.error(f"Failed to parse message: {e}")
                    logger.debug(f"Raw message: {line}")
                    
        except EndOfStream:
            logger.info("📥 STDIN closed")
        except Exception as e:
            logger.error(f"STDIN reader error: {e}")
        finally:
            await self._read_stream_writer.aclose()
    
    async def stdout_writer(self) -> None:
        """
        STDOUT으로 JSON-RPC 메시지 쓰기
        
        처리 과정:
        1. 쓰기 스트림에서 메시지 수신
        2. JSON으로 직렬화
        3. STDOUT에 라인 단위 출력 + 플러시
        """
        _, stdout = self.create_stdio_streams()
        
        try:
            async for session_message in self._write_stream_reader:
                try:
                    # JSON-RPC 메시지 직렬화
                    json_line = session_message.to_json()
                    await stdout.write(json_line + "\n")
                    await stdout.flush()
                    
                    logger.debug(f"📤 Sent message: {session_message.message.model_dump().get('method', 'response')}")
                    
                except Exception as e:
                    logger.error(f"Failed to write message: {e}")
                    
        except EndOfStream:
            logger.info("📤 STDOUT closed")
        except Exception as e:
            logger.error(f"[ERROR] STDOUT writer error: {e}")
    
    async def send_message(self, session_message: SessionMessage) -> None:
        """메시지 전송"""
        if not self.write_stream:
            raise RuntimeError("Write stream not initialized")
            
        await self.write_stream.send(session_message)
    
    async def receive_message(self) -> SessionMessage:
        """메시지 수신"""
        if not self.read_stream:
            raise RuntimeError("Read stream not initialized")
            
        return await self.read_stream.receive()
    
    async def close(self) -> None:
        """스트림 정리"""
        try:
            if self._read_stream_writer:
                await self._read_stream_writer.aclose()
            if self.write_stream:
                await self.write_stream.aclose()
            logger.info("✅ Transport streams closed")
        except Exception as e:
            logger.error(f"[ERROR] Error closing transport: {e}")

class STDIOServer:
    """
    STDIO 서버 컨텍스트 매니저
    
    공식 패턴 기반:
    - anyio.create_task_group으로 동시 실행
    - stdin_reader, stdout_writer, message_processor 병렬 처리
    """
    
    def __init__(self, message_handler):
        self.transport = STDIOTransport()
        self.message_handler = message_handler
        
    async def __aenter__(self):
        await self.transport.initialize_streams()
        return self.transport
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.transport.close()
        
    async def run(self) -> None:
        """
        STDIO 서버 실행
        
        Task Group으로 3개 작업 병렬 실행:
        1. stdin_reader: STDIN 읽기
        2. stdout_writer: STDOUT 쓰기  
        3. message_processor: 메시지 처리
        """
        try:
            async with self:
                async with anyio.create_task_group() as tg:
                    # ✅ 공식 패턴: anyio Task Group 사용
                    tg.start_soon(self.transport.stdin_reader)
                    tg.start_soon(self.transport.stdout_writer) 
                    tg.start_soon(self._message_processor)
                    
                    logger.info("🚀 STDIO server running with 3 concurrent tasks")
        except KeyboardInterrupt:
            # KeyboardInterrupt를 조용히 처리 (상위로 전파하지 않음)
            logger.info("[PROCESS] Graceful shutdown initiated")
            raise
        except CancelledError:
            # anyio TaskGroup 취소를 조용히 처리
            logger.info("[PROCESS] Tasks cancelled for shutdown")
            raise
    
    async def _message_processor(self) -> None:
        """메시지 처리 루프"""
        try:
            while True:
                # 메시지 수신 대기
                session_message = await self.transport.receive_message()
                
                # 메시지 핸들러에 전달
                response = await self.message_handler(session_message)
                
                # 응답이 있으면 전송
                if response:
                    await self.transport.send_message(response)
                    
        except EndOfStream:
            logger.info("🔚 Message processor ended")
        except Exception as e:
            logger.error(f"[ERROR] Message processor error: {e}")

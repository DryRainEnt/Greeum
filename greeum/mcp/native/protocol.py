#!/usr/bin/env python3
"""
Greeum Native MCP Server - JSON-RPC Protocol Processor
JSON-RPC 2.0 및 MCP 프로토콜 메시지 처리

핵심 기능:
- JSON-RPC 2.0 스펙 완전 준수
- MCP 프로토콜 메시지 라우팅
- 안전한 에러 처리 및 응답 생성
- Pydantic 기반 타입 안전성
"""

import logging
from typing import Any, Dict, Optional, Union
from .types import (
    SessionMessage, JSONRPCRequest, JSONRPCResponse, JSONRPCErrorResponse,
    JSONRPCNotification, JSONRPCError, ErrorCodes,
    InitializeParams, InitializeResult, Capabilities, ServerInfo,
    ToolsListResult, ToolCallParams, ToolResult, TextContent
)

logger = logging.getLogger("greeum_native_protocol")

class JSONRPCProcessor:
    """
    JSON-RPC 2.0 메시지 프로세서
    
    MCP 프로토콜 지원 메서드:
    - initialize: 서버 초기화
    - initialized: 초기화 완료 통지
    - tools/list: 도구 목록 조회
    - tools/call: 도구 실행
    """
    
    def __init__(self, tool_handler):
        self.tool_handler = tool_handler
        self.initialized = False
        
    async def process_message(self, session_message: SessionMessage) -> Optional[SessionMessage]:
        """
        JSON-RPC 메시지 처리 메인 라우터
        
        Args:
            session_message: 수신된 세션 메시지
            
        Returns:
            Optional[SessionMessage]: 응답 메시지 (알림의 경우 None)
        """
        message = session_message.message
        
        # 알림 메시지 (응답 없음)
        if isinstance(message, JSONRPCNotification):
            await self._handle_notification(message)
            return None
            
        # 요청 메시지 (응답 필요)
        if isinstance(message, JSONRPCRequest):
            return await self._handle_request(message)
            
        # 응답/에러 메시지 (클라이언트가 보낸 응답 - 일반적으로 처리 안 함)
        logger.warning(f"Unexpected message type: {type(message)}")
        return None
    
    async def _handle_notification(self, notification: JSONRPCNotification) -> None:
        """알림 메시지 처리"""
        method = notification.method
        params = notification.params or {}
        
        if method == "initialized":
            # 클라이언트가 초기화 완료를 통지
            self.initialized = True
            logger.info("Client initialization completed")
        else:
            logger.warning(f"Unknown notification method: {method}")
    
    async def _handle_request(self, request: JSONRPCRequest) -> SessionMessage:
        """요청 메시지 처리"""
        method = request.method
        params = request.params or {}
        request_id = request.id
        
        try:
            # MCP 프로토콜 메서드 라우팅
            if method == "initialize":
                result = await self._handle_initialize(params)
            elif method == "tools/list":
                result = await self._handle_tools_list(params)
            elif method == "tools/call":
                result = await self._handle_tools_call(params)
            else:
                # 지원하지 않는 메서드
                return self._create_error_response(
                    request_id, 
                    ErrorCodes.METHOD_NOT_FOUND,
                    f"Method not found: {method}"
                )
            
            # 성공 응답 생성
            return self._create_success_response(request_id, result)
            
        except ValueError as e:
            # 파라미터 유효성 검사 실패
            return self._create_error_response(
                request_id,
                ErrorCodes.INVALID_PARAMS,
                str(e)
            )
        except Exception as e:
            # 내부 서버 에러
            logger.error(f"Internal error in {method}: {e}")
            return self._create_error_response(
                request_id,
                ErrorCodes.INTERNAL_ERROR,
                "Internal server error"
            )
    
    async def _handle_initialize(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        initialize 메서드 처리
        
        MCP 초기화 프로토콜:
        1. 클라이언트가 프로토콜 버전과 기능을 전송
        2. 서버가 지원 기능과 서버 정보를 응답
        """
        try:
            # 파라미터 검증
            init_params = InitializeParams.model_validate(params)
            logger.info(f"📋 Initialize request from {init_params.clientInfo.name} v{init_params.clientInfo.version}")
            
            # 프로토콜 버전 검사
            if not init_params.protocolVersion.startswith("2025-"):
                logger.warning(f"Unsupported protocol version: {init_params.protocolVersion}")
            
            # 서버 기능 정의
            server_capabilities = Capabilities(
                tools={
                    "listChanged": False  # 도구 목록이 동적으로 변경되지 않음
                },
                resources={},  # 리소스 지원 안 함
                prompts={},    # 프롬프트 지원 안 함
                logging={}     # 로깅 지원 안 함
            )
            
            # 초기화 결과 생성
            result = InitializeResult(
                protocolVersion="2025-03-26",
                capabilities=server_capabilities,
                serverInfo=ServerInfo()
            )
            
            logger.info("Server initialization completed")
            return result.model_dump()
            
        except Exception as e:
            logger.error(f"Initialize failed: {e}")
            raise ValueError(f"Invalid initialize parameters: {e}")
    
    async def _handle_tools_list(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        tools/list 메서드 처리
        
        Greeum MCP 도구 목록 반환:
        - add_memory: 메모리 추가
        - search_memory: 메모리 검색  
        - get_memory_stats: 메모리 통계
        - usage_analytics: 사용 분석
        """
        # 도구 목록 정의 (OpenAPI 스키마 형식)
        tools = [
            {
                "name": "add_memory",
                "description": "Add important permanent memories to long-term storage.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "content": {
                            "type": "string",
                            "description": "Content to store in memory"
                        },
                        "importance": {
                            "type": "number",
                            "description": "Importance score (0.0-1.0)",
                            "minimum": 0.0,
                            "maximum": 1.0,
                            "default": 0.5
                        }
                    },
                    "required": ["content"]
                }
            },
            {
                "name": "search_memory", 
                "description": "Search existing memories using keywords or semantic similarity.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Search query"
                        },
                        "limit": {
                            "type": "integer",
                            "description": "Maximum number of results",
                            "minimum": 1,
                            "maximum": 50,
                            "default": 5
                        }
                    },
                    "required": ["query"]
                }
            },
            {
                "name": "get_memory_stats",
                "description": "Get current memory system statistics and health status.",
                "inputSchema": {
                    "type": "object",
                    "properties": {}
                }
            },
            {
                "name": "usage_analytics",
                "description": "Get comprehensive usage analytics and insights.",
                "inputSchema": {
                    "type": "object", 
                    "properties": {
                        "days": {
                            "type": "integer",
                            "description": "Analysis period in days",
                            "minimum": 1,
                            "maximum": 90,
                            "default": 7
                        },
                        "report_type": {
                            "type": "string",
                            "description": "Report type",
                            "enum": ["usage", "quality", "performance", "all"],
                            "default": "usage"
                        }
                    }
                }
            }
        ]
        
        result = {"tools": tools}
        logger.info(f"📋 Listed {len(tools)} tools")
        return result
    
    async def _handle_tools_call(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        tools/call 메서드 처리
        
        도구 실행:
        1. 파라미터 검증
        2. 도구 핸들러에 위임
        3. 결과를 MCP 형식으로 래핑
        """
        try:
            # 파라미터 검증
            tool_call = ToolCallParams.model_validate(params)
            tool_name = tool_call.name
            tool_args = tool_call.arguments or {}
            
            logger.info(f"Calling tool: {tool_name}")
            
            # 도구 실행
            result_text = await self.tool_handler.execute_tool(tool_name, tool_args)
            
            # MCP 형식 결과 생성
            result = ToolResult(
                content=[TextContent(text=result_text)],
                isError=False
            )
            
            logger.info(f"Tool {tool_name} executed successfully")
            return result.model_dump()
            
        except ValueError as e:
            # 도구 실행 실패 - 에러 결과 반환
            error_text = f"Tool execution failed: {e}"
            result = ToolResult(
                content=[TextContent(text=error_text)],
                isError=True
            )
            logger.error(error_text)
            return result.model_dump()
        except Exception as e:
            # 예상치 못한 에러
            error_text = f"Unexpected error: {e}"
            result = ToolResult(
                content=[TextContent(text=error_text)],
                isError=True
            )
            logger.error(error_text)
            return result.model_dump()
    
    def _create_success_response(self, request_id: Any, result: Any) -> SessionMessage:
        """성공 응답 생성"""
        response = JSONRPCResponse(id=request_id, result=result)
        return SessionMessage(message=response)
    
    def _create_error_response(self, request_id: Any, code: int, message: str, data: Any = None) -> SessionMessage:
        """에러 응답 생성"""
        error = JSONRPCError(code=code, message=message, data=data)
        response = JSONRPCErrorResponse(id=request_id, error=error)
        return SessionMessage(message=response)
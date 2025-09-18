#!/usr/bin/env python3
"""
Greeum Native MCP Server - Pydantic Type Definitions
JSON-RPC 2.0 및 MCP 프로토콜 타입 정의

공식 패턴 기반:
- Anthropic MCP Python SDK 타입 구조 준수
- Pydantic v2 기반 안전한 검증/직렬화
- MCP Protocol Revision: 2025-03-26 준수
"""

from typing import Any, Dict, List, Optional, Union, Literal
from pydantic import BaseModel, Field
import uuid

# 중앙화된 버전 참조
def _get_version() -> str:
    """중앙화된 버전 참조"""
    try:
        from greeum import __version__
        return __version__
    except ImportError:
        return "unknown"

# =============================================================================
# JSON-RPC 2.0 Base Types
# =============================================================================

class JSONRPCMessage(BaseModel):
    """JSON-RPC 2.0 기본 메시지"""
    jsonrpc: Literal["2.0"] = "2.0"

class JSONRPCRequest(JSONRPCMessage):
    """JSON-RPC 2.0 요청"""
    id: Union[str, int, None] = None
    method: str
    params: Optional[Dict[str, Any]] = None

class JSONRPCResponse(JSONRPCMessage):
    """JSON-RPC 2.0 성공 응답"""
    id: Union[str, int, None] = None
    result: Any

class JSONRPCError(BaseModel):
    """JSON-RPC 2.0 에러 상세"""
    code: int
    message: str
    data: Optional[Any] = None

class JSONRPCErrorResponse(JSONRPCMessage):
    """JSON-RPC 2.0 에러 응답"""
    id: Union[str, int, None] = None
    error: JSONRPCError

class JSONRPCNotification(JSONRPCMessage):
    """JSON-RPC 2.0 알림 (응답 없음)"""
    method: str
    params: Optional[Dict[str, Any]] = None

# =============================================================================
# MCP Protocol Types
# =============================================================================

class ClientInfo(BaseModel):
    """클라이언트 정보"""
    name: str
    version: str

class ServerInfo(BaseModel):
    """서버 정보"""
    name: str = "Greeum Memory System"
    version: str = Field(default_factory=_get_version)

class Capabilities(BaseModel):
    """MCP 기능 목록"""
    tools: Optional[Dict[str, Any]] = Field(default_factory=dict)
    resources: Optional[Dict[str, Any]] = Field(default_factory=dict)
    prompts: Optional[Dict[str, Any]] = Field(default_factory=dict)
    logging: Optional[Dict[str, Any]] = Field(default_factory=dict)

# =============================================================================
# MCP Initialize Protocol
# =============================================================================

class InitializeParams(BaseModel):
    """Initialize 요청 파라미터"""
    protocolVersion: str
    capabilities: Capabilities
    clientInfo: ClientInfo

class InitializeResult(BaseModel):
    """Initialize 응답 결과"""
    protocolVersion: str = "2025-03-26"
    capabilities: Capabilities
    serverInfo: ServerInfo

# =============================================================================
# MCP Tools Protocol  
# =============================================================================

class ToolInfo(BaseModel):
    """도구 정보"""
    name: str
    description: str
    inputSchema: Dict[str, Any]

class ToolsListResult(BaseModel):
    """Tools/list 응답"""
    tools: List[ToolInfo]

class ToolCallParams(BaseModel):
    """Tools/call 요청 파라미터"""
    name: str
    arguments: Optional[Dict[str, Any]] = None

class TextContent(BaseModel):
    """텍스트 컨텐츠"""
    type: Literal["text"] = "text"
    text: str

class ToolResult(BaseModel):
    """도구 실행 결과"""
    content: List[TextContent]
    isError: Optional[bool] = None

# =============================================================================
# MCP Resources Protocol (향후 확장용)
# =============================================================================

class ResourceInfo(BaseModel):
    """리소스 정보"""
    uri: str
    name: str
    description: Optional[str] = None
    mimeType: Optional[str] = None

class ResourcesListResult(BaseModel):
    """Resources/list 응답"""
    resources: List[ResourceInfo]

# =============================================================================
# MCP Prompts Protocol (향후 확장용)
# =============================================================================

class PromptInfo(BaseModel):
    """프롬프트 정보"""
    name: str
    description: Optional[str] = None
    arguments: Optional[List[Dict[str, Any]]] = None

class PromptsListResult(BaseModel):
    """Prompts/list 응답"""
    prompts: List[PromptInfo]

# =============================================================================
# Session Message Wrapper
# =============================================================================

class SessionMessage(BaseModel):
    """세션 메시지 래퍼 (공식 SDK 패턴)"""
    message: Union[JSONRPCRequest, JSONRPCResponse, JSONRPCErrorResponse, JSONRPCNotification]

    @classmethod
    def from_json(cls, json_str: str) -> "SessionMessage":
        """JSON 문자열에서 SessionMessage 생성"""
        import json
        data = json.loads(json_str)
        return cls.from_dict(data)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SessionMessage":
        """사전 객체에서 SessionMessage 생성"""
        
        # 메시지 타입 구분
        if "method" in data:
            if "id" in data:
                message = JSONRPCRequest.model_validate(data)
            else:
                message = JSONRPCNotification.model_validate(data)
        elif "error" in data:
            message = JSONRPCErrorResponse.model_validate(data)
        else:
            message = JSONRPCResponse.model_validate(data)

        return cls(message=message)

    def to_json(self) -> str:
        """JSON 문자열로 변환"""
        return self.message.model_dump_json()

    def to_dict(self) -> Dict[str, Any]:
        """사전 객체로 변환"""
        return self.message.model_dump(mode="json")

# =============================================================================
# Greeum Tool Schemas
# =============================================================================

class AddMemoryArgs(BaseModel):
    """add_memory 도구 인자"""
    content: str = Field(description="Content to store in memory")
    importance: Optional[float] = Field(default=0.5, description="Importance score (0.0-1.0)")

class SearchMemoryArgs(BaseModel):
    """search_memory 도구 인자"""
    query: str = Field(description="Search query")
    limit: Optional[int] = Field(default=5, description="Maximum number of results")

class GetMemoryStatsArgs(BaseModel):
    """get_memory_stats 도구 인자"""
    pass  # 파라미터 없음

class UsageAnalyticsArgs(BaseModel):
    """usage_analytics 도구 인자"""
    days: Optional[int] = Field(default=7, description="Analysis period in days")
    report_type: Optional[str] = Field(default="usage", description="Report type")

# =============================================================================
# Error Codes (JSON-RPC 2.0 + MCP 확장)
# =============================================================================

class ErrorCodes:
    """에러 코드 상수"""
    # JSON-RPC 2.0 표준 에러
    PARSE_ERROR = -32700
    INVALID_REQUEST = -32600
    METHOD_NOT_FOUND = -32601
    INVALID_PARAMS = -32602
    INTERNAL_ERROR = -32603
    
    # MCP 확장 에러
    INITIALIZATION_FAILED = -32000
    TOOL_EXECUTION_FAILED = -32001
    RESOURCE_NOT_FOUND = -32002
    CAPABILITY_NOT_SUPPORTED = -32003

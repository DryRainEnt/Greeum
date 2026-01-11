#!/usr/bin/env python3
"""
Native MCP Server - v2.2.9 Hotfix
Claude Desktop 직접 연동을 위한 네이티브 JSON-RPC 2.0 MCP 서버

🎯 목표:
- FastMCP asyncio 충돌 완전 해결
- MCP 표준 100% 준수
- Claude Desktop 완벽 호환
- BaseAdapter 로직 100% 재사용

🔧 기술적 접근:
- 네이티브 JSON-RPC 2.0 구현
- 직접 stdin/stdout 처리 
- asyncio 충돌 원천 차단
- 기존 비즈니스 로직 완전 재사용
"""

import json
import sys
import logging
from typing import Dict, Any, Optional

# BaseAdapter에서 완전히 검증된 로직 재사용
try:
    from .adapters.base_adapter import BaseAdapter
except ImportError:
    # 직접 실행시 절대경로 사용
    import sys
    import os
    current_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(current_dir)
    sys.path.insert(0, parent_dir)
    from adapters.base_adapter import BaseAdapter

# 명령행 인수 처리
DEBUG_MODE = "--debug" in sys.argv
VERBOSE_MODE = "--verbose" in sys.argv or "-v" in sys.argv

# 로깅 설정 - stderr로만 출력 (stdout 오염 방지)
if DEBUG_MODE:
    log_level = logging.DEBUG
    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
elif VERBOSE_MODE:
    log_level = logging.INFO
    log_format = '%(levelname)s:%(name)s:%(message)s'
else:
    log_level = logging.WARNING
    log_format = '%(levelname)s:%(name)s:%(message)s'

logging.basicConfig(level=log_level, stream=sys.stderr, format=log_format)
logger = logging.getLogger("native_mcp")

class GreaumAdapter(BaseAdapter):
    """Native MCP용 BaseAdapter 구현"""
    async def run(self):
        """BaseAdapter 추상 메서드 구현 (실제로는 사용하지 않음)"""
        pass

class NativeMCPServer:
    """네이티브 MCP 서버 - JSON-RPC 2.0 직접 구현"""
    
    def __init__(self):
        """서버 초기화 - BaseAdapter 활용"""
        self.adapter = GreaumAdapter()
        self.server_info = {
            "name": "Greeum Memory System", 
            "version": "2.2.8a1"
        }
        
        # BaseAdapter 컴포넌트 초기화
        components = self.adapter.initialize_greeum_components()
        if not components:
            logger.error("[ERROR] Failed to initialize Greeum components")
            raise RuntimeError("Greeum components initialization failed")
        
        logger.info("✅ Native MCP Server initialized with BaseAdapter")
    
    def create_success_response(self, request_id: Any, result: Any) -> Dict[str, Any]:
        """성공 응답 생성 - MCP 표준 준수"""
        response = {
            "jsonrpc": "2.0",
            "result": result
        }
        if request_id is not None:
            response["id"] = request_id
        return response
    
    def create_error_response(self, request_id: Any, code: int, message: str) -> Dict[str, Any]:
        """에러 응답 생성 - MCP 표준 준수"""
        response = {
            "jsonrpc": "2.0",
            "error": {
                "code": code,
                "message": message
            }
        }
        if request_id is not None:
            response["id"] = request_id
        return response
    
    def handle_initialize(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """MCP Initialize 처리"""
        request_id = request.get("id")
        
        result = {
            "protocolVersion": "2024-11-05",
            "capabilities": {
                "tools": {}
            },
            "serverInfo": self.server_info
        }
        
        return self.create_success_response(request_id, result)
    
    def handle_tools_list(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """MCP Tools List 처리"""
        request_id = request.get("id")
        
        tools = [
            {
                "name": "add_memory",
                "description": "[MEMORY] Add important permanent memories to long-term storage.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "content": {
                            "type": "string", 
                            "description": "Memory content (be specific and meaningful, min 10 chars)"
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
                "description": "🔍 Search existing memories using keywords or semantic similarity with association expansion.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Search query (use specific keywords)"
                        },
                        "limit": {
                            "type": "integer",
                            "description": "Maximum results (5-10 recommended)",
                            "minimum": 1,
                            "maximum": 50,
                            "default": 5
                        },
                        "depth": {
                            "type": "integer",
                            "description": "Association expansion depth (0=basic, 1-3=expand with associations)",
                            "minimum": 0,
                            "maximum": 3,
                            "default": 0
                        },
                        "tolerance": {
                            "type": "number",
                            "description": "Search tolerance (0.0=strict, 1.0=lenient)",
                            "minimum": 0.0,
                            "maximum": 1.0,
                            "default": 0.5
                        }
                    },
                    "required": ["query"]
                }
            },
            {
                "name": "get_memory_stats",
                "description": "📊 Get current memory system statistics and health status.",
                "inputSchema": {
                    "type": "object",
                    "properties": {}
                }
            },
            {
                "name": "usage_analytics",
                "description": "📊 Get comprehensive usage analytics and insights.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "days": {
                            "type": "integer",
                            "description": "Analysis period in days (1-90)",
                            "minimum": 1,
                            "maximum": 90,
                            "default": 7
                        },
                        "report_type": {
                            "type": "string",
                            "description": "Type of analytics report",
                            "enum": ["usage", "quality", "performance", "all"],
                            "default": "usage"
                        }
                    }
                }
            },
            {
                "name": "search",
                "description": "🔍 Search for information in memory using keywords or semantic similarity.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Search query for finding relevant memories"
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
                "name": "fetch",
                "description": "📄 Fetch a specific memory block by ID or retrieve recent memories.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "block_id": {
                            "type": "string",
                            "description": "Specific block ID to retrieve"
                        },
                        "count": {
                            "type": "integer",
                            "description": "Number of recent memories to fetch if no block_id",
                            "minimum": 1,
                            "maximum": 50,
                            "default": 10
                        }
                    }
                }
            }
        ]
        
        result = {"tools": tools}
        return self.create_success_response(request_id, result)
    
    def handle_tools_call(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """MCP Tools Call 처리 - BaseAdapter 메서드 직접 활용"""
        request_id = request.get("id")
        
        try:
            params = request.get("params", {})
            tool_name = params.get("name")
            arguments = params.get("arguments", {})
            
            # BaseAdapter 메서드 호출 (이미 100% 검증된 로직)
            if tool_name == "add_memory":
                content = arguments.get("content", "")
                importance = arguments.get("importance", 0.5)
                result_text = self.adapter.add_memory_tool(content, importance)
                
            elif tool_name == "search_memory":
                query = arguments.get("query", "")
                limit = arguments.get("limit", 5)
                depth = arguments.get("depth", 0)
                tolerance = arguments.get("tolerance", 0.5)
                result_text = self.adapter.search_memory_tool(query, limit, depth, tolerance)
                
            elif tool_name == "get_memory_stats":
                result_text = self.adapter.get_memory_stats_tool()
                
            elif tool_name == "usage_analytics":
                days = arguments.get("days", 7)
                report_type = arguments.get("report_type", "usage")
                result_text = self.adapter.usage_analytics_tool(days, report_type)

            elif tool_name == "search":
                # OpenAI GPT 호환을 위한 search 래퍼 - search_memory로 리다이렉트
                query = arguments.get("query", "")
                limit = arguments.get("limit", 5)
                result_text = self.adapter.search_memory_tool(query, limit, 0, 0.5)

            elif tool_name == "fetch":
                # OpenAI GPT 호환을 위한 fetch 래퍼
                block_id = arguments.get("block_id")
                count = arguments.get("count", 10)

                if block_id:
                    # 특정 블록 조회 (간단 구현)
                    try:
                        # block_id를 이용해 검색
                        result_text = self.adapter.search_memory_tool(f"block_id:{block_id}", 1, 0, 0.9)
                    except:
                        result_text = f"Block #{block_id} not found"
                else:
                    # 최근 메모리들 조회
                    result_text = self.adapter.search_memory_tool("*", count, 0, 0.1)

            else:
                return self.create_error_response(request_id, -32601, f"Unknown tool: {tool_name}")
            
            # MCP 표준 응답 형식
            result = {
                "content": [
                    {
                        "type": "text",
                        "text": result_text
                    }
                ]
            }
            
            return self.create_success_response(request_id, result)
            
        except Exception as e:
            logger.error(f"Tool call failed: {e}")
            return self.create_error_response(request_id, -32603, f"Tool execution failed: {str(e)}")
    
    def process_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """요청 처리 - MCP 메서드 라우팅"""
        method = request.get("method")
        request_id = request.get("id")

        if method == "initialize":
            return self.handle_initialize(request)
        elif method == "tools/list":
            return self.handle_tools_list(request)
        elif method == "tools/call":
            return self.handle_tools_call(request)
        else:
            return self.create_error_response(request_id, -32601, f"Unknown method: {method}")

    @staticmethod
    def _read_jsonrpc_message() -> Optional[str]:
        """STDIO에서 JSON-RPC 메시지 읽기 (Content-Length 및 라인 기반 모두 지원)"""
        stdin_buffer = sys.stdin.buffer

        while True:
            line = stdin_buffer.readline()
            if not line:
                return None  # EOF

            line_str = line.decode("utf-8").strip()
            if not line_str:
                continue

            # Content-Length 헤더 감지
            if line_str.lower().startswith("content-length:"):
                try:
                    content_length = int(line_str.split(":", 1)[1].strip())
                except ValueError:
                    logger.warning(f"Invalid Content-Length value: {line_str}")
                    continue

                # 추가 헤더 건너뛰기
                while True:
                    header_line = stdin_buffer.readline()
                    if not header_line:
                        return None
                    if header_line.strip() == b"":
                        break

                if content_length <= 0:
                    logger.warning(f"Ignoring non-positive Content-Length: {content_length}")
                    continue

                payload = stdin_buffer.read(content_length)
                if not payload:
                    return None

                return payload.decode("utf-8")

            # Content-Length 헤더가 없으면 그대로 JSON 라인으로 처리
            return line_str

    @staticmethod
    def _write_jsonrpc_message(message: Dict[str, Any]) -> None:
        """JSON-RPC 메시지를 STDOUT으로 전송 (라인 기반)"""
        print(json.dumps(message, ensure_ascii=False), flush=True)

    def run_stdio(self):
        """stdin/stdout 직접 처리 - asyncio 없음, BrokenPipe 처리"""
        logger.info("🚀 Starting Native MCP server on stdio...")
        logger.info("✅ All tools registered: add_memory, search_memory, get_memory_stats, usage_analytics")
        
        # MCP 클라이언트를 위한 명확한 준비 신호 출력
        print("MCP_SERVER_READY", file=sys.stderr, flush=True)
        if DEBUG_MODE:
            logger.debug("🔍 Debug mode enabled - detailed logging active")
        if VERBOSE_MODE:
            logger.info("📢 Verbose mode enabled - enhanced logging active")
        
        try:
            while True:
                try:
                    raw_message = self._read_jsonrpc_message()
                    if raw_message is None:
                        logger.info("🛑 EOF received - shutting down")
                        break

                    try:
                        # JSON-RPC 요청 파싱
                        request = json.loads(raw_message)
                        request_id = request.get("id")
                        method = request.get("method")
                        logger.debug(
                            "Received request %s (id=%s): %s",
                            method,
                            request_id,
                            raw_message[:200],
                        )

                        # 요청 처리
                        response = self.process_request(request)

                        # Notifications (id 없음) 는 응답하지 않음
                        if request_id is None:
                            continue

                        # JSON-RPC 응답 전송
                        try:
                            self._write_jsonrpc_message(response)
                            logger.debug(
                                "Sent response for id=%s: %s",
                                request_id,
                                json.dumps(response, ensure_ascii=False)[:200],
                            )
                        except BrokenPipeError:
                            logger.info("🛑 Client disconnected")
                            break

                    except json.JSONDecodeError as e:
                        # JSON 파싱 에러
                        logger.warning("Parse error decoding message: %s", raw_message[:200])
                        error_response = self.create_error_response(None, -32700, f"Parse error: {str(e)}")
                        try:
                            self._write_jsonrpc_message(error_response)
                        except BrokenPipeError:
                            logger.info("🛑 Client disconnected during error response")
                            break

                    except Exception as e:
                        # 일반 에러
                        logger.error(f"Request processing error: {e}")
                        request_id = request.get("id") if 'request' in locals() else None
                        if request_id is None:
                            continue
                        error_response = self.create_error_response(request_id, -32603, f"Internal error: {str(e)}")
                        try:
                            self._write_jsonrpc_message(error_response)
                        except BrokenPipeError:
                            logger.info("🛑 Client disconnected during error response")
                            break

                except EOFError:
                    logger.info("🛑 EOFError - client disconnected")
                    break
                except BrokenPipeError:
                    logger.info("🛑 BrokenPipe - client disconnected") 
                    break

        except KeyboardInterrupt:
            logger.info("🛑 Server shutdown requested (Ctrl+C)")
        except Exception as e:
            logger.error(f"[ERROR] Server error: {e}")
            raise

def main():
    """서버 메인 실행"""
    try:
        # 시작 로그 출력
        if DEBUG_MODE:
            logger.debug("🔧 Starting Greeum MCP Server in DEBUG mode")
        elif VERBOSE_MODE:
            logger.info("📢 Starting Greeum MCP Server in VERBOSE mode")
        else:
            logger.info("🚀 Starting Greeum MCP Server")
            
        server = NativeMCPServer()
        server.run_stdio()
    except Exception as e:
        logger.error(f"[ERROR] Failed to start server: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()

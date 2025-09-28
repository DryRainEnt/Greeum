#!/usr/bin/env python3
"""
JSON-RPC 어댑터 - macOS/Linux 환경 전용
- 직접 JSON-RPC 2.0 프로토콜 구현
- 기존 claude_code_mcp_server.py의 안정적 로직 활용
- stdin/stdout 기반 표준 MCP 통신
"""

import asyncio
import json
import logging
import sys
from typing import Dict, Any, Optional
from datetime import datetime

from .base_adapter import BaseAdapter

logger = logging.getLogger(__name__)

class JSONRPCAdapter(BaseAdapter):
    """macOS/Linux 환경용 JSON-RPC 직접 구현 어댑터"""
    
    def __init__(self):
        super().__init__()
        self.server_info = {
            "name": "Greeum",
            "version": "2.2.7"
        }
        
    async def run(self):
        """JSON-RPC 서버 실행"""
        try:
            # Greeum 컴포넌트 사전 초기화
            components = self.initialize_greeum_components()
            if not components:
                logger.error("[ERROR] Cannot start server: Greeum components unavailable")
                sys.exit(1)
            
            # GREEUM_QUIET 환경변수 지원
            import os
            if not os.getenv('GREEUM_QUIET'):
                logger.info("🚀 Starting JSON-RPC adapter for macOS/Linux...")
                logger.info("✅ All tools ready and Greeum components initialized")
            
            # JSON-RPC 메시지 루프
            await self._message_loop()
            
        except Exception as e:
            logger.error(f"[ERROR] JSON-RPC adapter failed: {e}")
            raise
    
    async def _message_loop(self):
        """JSON-RPC 메시지 처리 루프"""
        try:
            while True:
                try:
                    # stdin에서 한 줄 읽기 (비동기)
                    line = await asyncio.get_event_loop().run_in_executor(
                        None, sys.stdin.readline
                    )
                    
                    if not line:
                        logger.info("👋 JSON-RPC adapter: EOF received")
                        break
                        
                    line = line.strip()
                    if not line:
                        continue
                    
                    # JSON 파싱 및 요청 처리
                    try:
                        request = json.loads(line)
                        response = await self._handle_request(request)
                        
                        if response:
                            # 응답 전송
                            response_json = json.dumps(response)
                            print(response_json, flush=True)
                            
                    except json.JSONDecodeError as e:
                        logger.error(f"JSON decode error: {e}")
                        error_response = {
                            "jsonrpc": "2.0",
                            "id": None,
                            "error": {
                                "code": -32700,
                                "message": "Parse error"
                            }
                        }
                        print(json.dumps(error_response), flush=True)
                        
                except Exception as e:
                    logger.error(f"Message loop error: {e}")
                    continue
                    
        except KeyboardInterrupt:
            logger.info("👋 JSON-RPC adapter stopped by user")
        except Exception as e:
            logger.error(f"Fatal error in message loop: {e}")
            raise
    
    async def _handle_request(self, request: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """JSON-RPC 요청 처리"""
        try:
            # 기본 JSON-RPC 검증
            if request.get("jsonrpc") != "2.0":
                return self._error_response(
                    request.get("id"), -32600, "Invalid Request"
                )
            
            method = request.get("method")
            request_id = request.get("id")
            params = request.get("params", {})
            
            logger.debug(f"Handling request: {method}")
            
            # 메서드별 처리
            if method == "initialize":
                return await self._handle_initialize(request_id, params)
            elif method == "tools/list":
                return await self._handle_tools_list(request_id)
            elif method == "tools/call":
                return await self._handle_tools_call(request_id, params)
            else:
                return self._error_response(
                    request_id, -32601, f"Method not found: {method}"
                )
                
        except Exception as e:
            logger.error(f"Request handling error: {e}")
            return self._error_response(
                request.get("id"), -32603, f"Internal error: {str(e)}"
            )
    
    async def _handle_initialize(self, request_id: int, params: Dict[str, Any]) -> Dict[str, Any]:
        """Initialize 요청 처리"""
        protocol_version = params.get("protocolVersion")
        client_info = params.get("clientInfo", {})
        
        logger.info(f"Initialize request from {client_info.get('name', 'Unknown')} v{client_info.get('version', 'Unknown')}")
        
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "result": {
                "protocolVersion": protocol_version or "2024-11-05",
                "capabilities": {
                    "tools": {}
                },
                "serverInfo": self.server_info
            }
        }
    
    async def _handle_tools_list(self, request_id: int) -> Dict[str, Any]:
        """Tools list 요청 처리"""
        tools = [
            {
                "name": "add_memory",
                "description": "[MEMORY] Add important permanent memories to long-term storage",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "content": {
                            "type": "string",
                            "description": "Memory content to store"
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
                "description": "🔍 Search existing memories using keywords or semantic similarity",
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
                "description": "📊 Get current memory system statistics and health status",
                "inputSchema": {
                    "type": "object",
                    "properties": {}
                }
            },
            {
                "name": "usage_analytics",
                "description": "📊 Get comprehensive usage analytics and insights",
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
                            "description": "Type of analytics report",
                            "enum": ["usage", "quality", "performance", "all"],
                            "default": "usage"
                        }
                    }
                }
            },
            {
                "name": "analyze",
                "description": "🧭 Summarize slots, branches, and recent activity",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "days": {
                            "type": "integer",
                            "description": "Look-back window in days",
                            "minimum": 1,
                            "maximum": 90,
                            "default": 7
                        }
                    }
                }
            }
        ]
        
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "result": {"tools": tools}
        }
    
    async def _handle_tools_call(self, request_id: int, params: Dict[str, Any]) -> Dict[str, Any]:
        """Tools call 요청 처리"""
        try:
            tool_name = params.get("name")
            arguments = params.get("arguments", {})
            
            if not tool_name:
                return self._error_response(request_id, -32602, "Missing tool name")
            
            # 도구 실행
            result_text = None
            
            if tool_name == "add_memory":
                content = arguments.get("content")
                if not content:
                    return self._error_response(request_id, -32602, "Missing required parameter: content")
                
                importance = arguments.get("importance", 0.5)
                result_text = self.add_memory_tool(content, importance)
                
            elif tool_name == "search_memory":
                query = arguments.get("query")
                if not query:
                    return self._error_response(request_id, -32602, "Missing required parameter: query")
                
                limit = arguments.get("limit", 5)
                result_text = self.search_memory_tool(query, limit)
                
            elif tool_name == "get_memory_stats":
                result_text = self.get_memory_stats_tool()
                
            elif tool_name == "usage_analytics":
                days = arguments.get("days", 7)
                report_type = arguments.get("report_type", "usage")
                result_text = self.usage_analytics_tool(days, report_type)

            elif tool_name == "analyze":
                days = arguments.get("days", 7)
                result_text = self.analyze_tool(days)

            else:
                return self._error_response(request_id, -32601, f"Unknown tool: {tool_name}")
            
            # 성공 응답
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {
                    "content": [
                        {
                            "type": "text",
                            "text": result_text
                        }
                    ]
                }
            }
            
        except Exception as e:
            logger.error(f"Tool execution error: {e}")
            return self._error_response(request_id, -32603, f"Tool execution failed: {str(e)}")
    
    def _error_response(self, request_id: Optional[int], code: int, message: str) -> Dict[str, Any]:
        """에러 응답 생성"""
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "error": {
                "code": code,
                "message": message
            }
        }

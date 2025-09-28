#!/usr/bin/env python3
"""
FastMCP 어댑터 - WSL/PowerShell 환경 전용
- FastMCP 프레임워크 기반으로 stdin/stdout 표준 처리
- WSL, PowerShell 등의 터미널 에뮬레이션 환경에서 안정적 작동
- AsyncIO 충돌 방지 및 런타임 안전성 보장
"""

import asyncio
import logging
import sys
from typing import Dict, Any

# FastMCP import with fallback
try:
    from mcp.server.fastmcp import FastMCP
    FASTMCP_AVAILABLE = True
except ImportError:
    FASTMCP_AVAILABLE = False

from .base_adapter import BaseAdapter

logger = logging.getLogger(__name__)

class FastMCPAdapter(BaseAdapter):
    """WSL/PowerShell 환경용 FastMCP 기반 어댑터"""
    
    def __init__(self):
        super().__init__()
        if not FASTMCP_AVAILABLE:
            raise ImportError("FastMCP not available. Install with: pip install mcp>=1.0.0")
        
        # FastMCP 앱 초기화
        self.app = FastMCP("Greeum Memory System")
        self.setup_tools()
        
    def setup_tools(self):
        """FastMCP 도구들 등록"""
        
        @self.app.tool()
        def add_memory(content: str, importance: float = 0.5) -> str:
            """[MEMORY] Add memories with v3 Branch/Slot priority storage.

            ⚠️  USAGE GUIDELINES:
            • ALWAYS search_memory first to avoid duplicates
            • Store meaningful information, not casual conversation
            • Use appropriate importance levels (see guide below)

            ✅ GOOD USES: user preferences, project details, decisions, recurring issues
            [ERROR] AVOID: greetings, weather, current time, temporary session info

            🎯 v3 FEATURES:
            • Auto-selects best slot based on similarity to heads
            • Stores as child of selected slot head (branch structure)
            • Returns metadata: slot, root, parent_block, storage_type
            • Integrates with STM for high-importance (≥0.7) immediate promotion

            🔍 WORKFLOW: search_memory → analyze results → add_memory (if truly new)
            """
            # Greeum 컴포넌트 초기화 (필요시)
            if not self.initialized:
                self.initialize_greeum_components()

            return self.add_memory_tool(content, importance)
        
        @self.app.tool()
        def search_memory(query: str, limit: int = 5, entry: str = "cursor", depth: int = 0) -> str:
            """🔍 Search memories with v3 Branch/Slot DFS priority system.

            ⚠️  ALWAYS USE THIS FIRST before add_memory to avoid duplicates!

            ✅ USE WHEN:
            • User mentions 'before', 'previous', 'remember'
            • Starting new conversation (check user context)
            • User asks about past discussions or projects
            • Before storing new information (duplicate check)

            🎯 v3 FEATURES:
            • entry="cursor" (default): Search from current cursor position
            • entry="head": Search from branch head
            • depth>0: Enable association expansion search
            • Returns metadata: search_type, entry_type, hops, time_ms

            🔍 SEARCH TIPS: Use specific keywords, try multiple terms if needed
            """
            if not self.initialized:
                self.initialize_greeum_components()

            return self.search_memory_tool(query, limit, depth, 0.5, entry)
        
        @self.app.tool()
        def get_memory_stats() -> str:
            """📊 Get current memory system statistics and health status.
            
            USE WHEN:
            • Starting new conversations (check user context)
            • Memory system seems slow or full
            • Debugging memory-related issues
            • Regular health checks
            
            💡 PROVIDES: File counts, sizes, system status
            """
            if not self.initialized:
                self.initialize_greeum_components()
                
            return self.get_memory_stats_tool()
        
        @self.app.tool()
        def usage_analytics(days: int = 7, report_type: str = "usage") -> str:
            """📊 Get comprehensive usage analytics and insights.

            USE FOR:
            • Understanding memory usage patterns
            • Identifying performance bottlenecks
            • Analyzing user behavior trends
            • System health monitoring
            
            💡 PROVIDES: Usage statistics, quality trends, performance insights
            """
            if not self.initialized:
                self.initialize_greeum_components()
                
            return self.usage_analytics_tool(days, report_type)

        @self.app.tool()
        def analyze(days: int = 7) -> str:
            """🧭 Generate branch/slot snapshot for quick situational awareness."""
            if not self.initialized:
                self.initialize_greeum_components()

            return self.analyze_tool(days)

        logger.info(
            "✅ FastMCP tools registered: add_memory, search_memory, get_memory_stats, usage_analytics, analyze"
        )
    
    async def run(self):
        """FastMCP 서버 실행 - AsyncIO 안전장치 포함"""
        try:
            # Greeum 컴포넌트 사전 초기화
            components = self.initialize_greeum_components()
            if not components:
                logger.error("[ERROR] Cannot start server: Greeum components unavailable")
                sys.exit(1)
            
            # GREEUM_QUIET 환경변수 지원
            import os
            if not os.getenv('GREEUM_QUIET'):
                logger.info("🚀 Starting FastMCP adapter for WSL/PowerShell...")
                logger.info("✅ All tools ready and Greeum components initialized")
            
            # FastMCP 서버 실행 (stdio transport)
            # 이미 이벤트 루프가 실행 중일 수 있으므로 안전장치 적용
            try:
                await self.app.run()
            except RuntimeError as e:
                if "Already running" in str(e):
                    logger.warning("⚠️  AsyncIO loop conflict detected, using alternative method")
                    # 대안: 현재 루프에서 직접 처리
                    await self._run_in_current_loop()
                else:
                    raise
                    
        except Exception as e:
            logger.error(f"[ERROR] FastMCP adapter failed: {e}")
            raise
    
    async def _run_in_current_loop(self):
        """현재 루프에서 안전하게 실행하는 대안 메서드"""
        try:
            # FastMCP의 내부 실행 로직을 우회하여 직접 처리
            logger.info("📡 Running FastMCP adapter in current event loop")
            
            # stdin/stdout을 통한 MCP 프로토콜 처리
            # (실제 구현에서는 FastMCP의 내부 로직 활용)
            import json
            
            while True:
                try:
                    # 표준 입력에서 JSON-RPC 메시지 읽기
                    line = await asyncio.get_event_loop().run_in_executor(None, sys.stdin.readline)
                    if not line:
                        break
                        
                    # JSON 파싱 및 처리
                    request = json.loads(line.strip())
                    response = await self._handle_request(request)
                    
                    # 응답 전송
                    if response:
                        print(json.dumps(response), flush=True)
                        
                except json.JSONDecodeError:
                    continue
                except Exception as e:
                    logger.error(f"Request handling error: {e}")
                    
        except KeyboardInterrupt:
            logger.info("👋 FastMCP adapter stopped")
    
    async def _handle_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """MCP 요청 처리 (간소화된 버전)"""
        try:
            method = request.get("method")
            request_id = request.get("id")
            
            if method == "initialize":
                return {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "result": {
                        "protocolVersion": "2024-11-05",
                        "capabilities": {"tools": {}},
                        "serverInfo": {"name": "Greeum", "version": "2.2.7"}
                    }
                }
            elif method == "tools/list":
                return {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "result": {"tools": [
                        {
                            "name": "add_memory",
                            "description": "Add memories with v3 Branch/Slot priority storage",
                            "inputSchema": {
                                "type": "object",
                                "properties": {
                                    "content": {"type": "string", "description": "Memory content"},
                                    "importance": {"type": "number", "default": 0.5, "minimum": 0.0, "maximum": 1.0}
                                },
                                "required": ["content"]
                            }
                        },
                        {
                            "name": "search_memory",
                            "description": "Search memories with v3 Branch/Slot DFS priority system",
                            "inputSchema": {
                                "type": "object",
                                "properties": {
                                    "query": {"type": "string", "description": "Search query"},
                                    "limit": {"type": "integer", "default": 5, "minimum": 1},
                                    "entry": {"type": "string", "default": "cursor", "enum": ["cursor", "head"]},
                                    "depth": {"type": "integer", "default": 0, "minimum": 0, "maximum": 3}
                                },
                                "required": ["query"]
                            }
                        },
                        {"name": "get_memory_stats", "description": "Get memory statistics"},
                        {"name": "usage_analytics", "description": "Get usage analytics"},
                        {"name": "analyze", "description": "Summarize slots and branches"}
                    ]}
                }
            elif method == "tools/call":
                params = request.get("params", {})
                tool_name = params.get("name")
                arguments = params.get("arguments", {})
                
                # 도구 실행
                if tool_name == "add_memory":
                    result = self.add_memory_tool(
                        arguments.get("content", ""),
                        arguments.get("importance", 0.5)
                    )
                elif tool_name == "search_memory":
                    result = self.search_memory_tool(
                        arguments.get("query", ""),
                        arguments.get("limit", 5),
                        arguments.get("depth", 0),
                        arguments.get("tolerance", 0.5),
                        arguments.get("entry", "cursor")
                    )
                elif tool_name == "get_memory_stats":
                    result = self.get_memory_stats_tool()
                elif tool_name == "usage_analytics":
                    result = self.usage_analytics_tool(
                        arguments.get("days", 7),
                        arguments.get("report_type", "usage")
                    )
                elif tool_name == "analyze":
                    result = self.analyze_tool(arguments.get("days", 7))
                else:
                    return {
                        "jsonrpc": "2.0",
                        "id": request_id,
                        "error": {"code": -32601, "message": f"Unknown tool: {tool_name}"}
                    }
                
                return {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "result": {"content": [{"type": "text", "text": result}]}
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Request handling error: {e}")
            return {
                "jsonrpc": "2.0",
                "id": request.get("id"),
                "error": {"code": -32603, "message": str(e)}
            }

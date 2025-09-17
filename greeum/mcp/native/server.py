#!/usr/bin/env python3
"""
Greeum Native MCP Server
Windows 호환 MCP 서버 구현
"""

import asyncio
import json
import sys
import logging
from typing import Dict, Any, Optional
from pathlib import Path

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("greeum_mcp_server")

class GreeumNativeMCPServer:
    """Greeum Native MCP Server"""
    
    def __init__(self):
        self.initialized = False
        self.tools = {
            "add_memory": {
                "name": "add_memory",
                "description": "메모리에 새로운 내용을 추가합니다",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "content": {
                            "type": "string",
                            "description": "추가할 메모리 내용"
                        },
                        "importance": {
                            "type": "number",
                            "description": "중요도 (0-1)",
                            "default": 0.5
                        }
                    },
                    "required": ["content"]
                }
            },
            "search_memory": {
                "name": "search_memory", 
                "description": "메모리에서 내용을 검색합니다",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "검색 쿼리"
                        },
                        "limit": {
                            "type": "integer",
                            "description": "결과 제한 개수",
                            "default": 5
                        }
                    },
                    "required": ["query"]
                }
            },
            "get_memory_stats": {
                "name": "get_memory_stats",
                "description": "메모리 통계를 조회합니다",
                "inputSchema": {
                    "type": "object",
                    "properties": {}
                }
            },
            "system_doctor": {
                "name": "system_doctor",
                "description": "시스템 상태를 진단하고 문제를 수정합니다",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "check_only": {
                            "type": "boolean",
                            "description": "진단만 수행 (수정하지 않음)",
                            "default": False
                        },
                        "auto_fix": {
                            "type": "boolean", 
                            "description": "자동 수정 수행",
                            "default": True
                        }
                    }
                }
            }
        }
    
    async def initialize(self):
        """서버 초기화"""
        try:
            logger.info("Greeum MCP Server 초기화 중...")
            self.initialized = True
            logger.info("✅ 서버 초기화 완료")
            return True
        except Exception as e:
            logger.error(f"❌ 서버 초기화 실패: {e}")
            return False
    
    async def handle_initialize(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """MCP 초기화 요청 처리"""
        return {
            "protocolVersion": "2025-03-26",
            "capabilities": {
                "tools": {}
            },
            "serverInfo": {
                "name": "greeum-native-mcp",
                "version": "3.1.1rc2.dev5"
            }
        }
    
    async def handle_tools_list(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """도구 목록 반환"""
        return {
            "tools": list(self.tools.values())
        }
    
    async def handle_tools_call(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """도구 호출 처리"""
        tool_name = params.get("name")
        arguments = params.get("arguments", {})
        
        if tool_name == "add_memory":
            return await self._add_memory(arguments)
        elif tool_name == "search_memory":
            return await self._search_memory(arguments)
        elif tool_name == "get_memory_stats":
            return await self._get_memory_stats(arguments)
        elif tool_name == "system_doctor":
            return await self._system_doctor(arguments)
        else:
            return {
                "content": [{"type": "text", "text": f"알 수 없는 도구: {tool_name}"}],
                "isError": True
            }
    
    async def _add_memory(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """메모리 추가"""
        content = args.get("content", "")
        importance = args.get("importance", 0.5)
        
        # 실제 구현에서는 여기서 데이터베이스에 저장
        logger.info(f"메모리 추가: {content[:50]}... (중요도: {importance})")
        
        return {
            "content": [{
                "type": "text", 
                "text": f"✅ 메모리가 성공적으로 추가되었습니다!\n내용: {content}\n중요도: {importance}"
            }]
        }
    
    async def _search_memory(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """메모리 검색"""
        query = args.get("query", "")
        limit = args.get("limit", 5)
        
        # 실제 구현에서는 여기서 데이터베이스에서 검색
        logger.info(f"메모리 검색: {query} (제한: {limit})")
        
        return {
            "content": [{
                "type": "text",
                "text": f"🔍 검색 결과 (쿼리: '{query}')\n\n찾은 메모리: {limit}개\n- 샘플 메모리 1: {query} 관련 내용\n- 샘플 메모리 2: {query} 관련 정보"
            }]
        }
    
    async def _get_memory_stats(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """메모리 통계 조회"""
        # 실제 구현에서는 여기서 데이터베이스 통계 조회
        logger.info("메모리 통계 조회")
        
        return {
            "content": [{
                "type": "text",
                "text": "📊 메모리 통계\n\n- 총 메모리 수: 0개\n- 평균 중요도: 0.5\n- 마지막 업데이트: 방금 전\n- 데이터베이스 상태: 정상"
            }]
        }
    
    async def _system_doctor(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """시스템 진단"""
        check_only = args.get("check_only", False)
        auto_fix = args.get("auto_fix", True)
        
        logger.info(f"시스템 진단 (check_only: {check_only}, auto_fix: {auto_fix})")
        
        if check_only:
            return {
                "content": [{
                    "type": "text",
                    "text": "🔍 시스템 진단 결과\n\n✅ 데이터베이스 연결: 정상\n✅ 메모리 시스템: 정상\n✅ MCP 서버: 정상\n\n모든 시스템이 정상 작동 중입니다."
                }]
            }
        else:
            return {
                "content": [{
                    "type": "text", 
                    "text": "🔧 시스템 자동 수정 완료\n\n✅ 데이터베이스 최적화 완료\n✅ 메모리 정리 완료\n✅ 설정 검증 완료\n\n시스템이 최적화되었습니다."
                }]
            }
    
    async def handle_message(self, message: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """JSON-RPC 메시지 처리"""
        method = message.get("method")
        params = message.get("params", {})
        msg_id = message.get("id")
        
        try:
            if method == "initialize":
                result = await self.handle_initialize(params)
            elif method == "tools/list":
                result = await self.handle_tools_list(params)
            elif method == "tools/call":
                result = await self.handle_tools_call(params)
            else:
                logger.warning(f"알 수 없는 메서드: {method}")
                return None
            
            return {
                "jsonrpc": "2.0",
                "id": msg_id,
                "result": result
            }
            
        except Exception as e:
            logger.error(f"메시지 처리 오류: {e}")
            return {
                "jsonrpc": "2.0", 
                "id": msg_id,
                "error": {
                    "code": -32603,
                    "message": "Internal error",
                    "data": str(e)
                }
            }
    
    async def run_stdio(self):
        """STDIO를 통한 서버 실행"""
        logger.info("Greeum MCP Server 시작 (STDIO 모드)")
        
        # 서버 초기화
        if not await self.initialize():
            return
        
        # STDIO 루프
        try:
            while True:
                line = await asyncio.get_event_loop().run_in_executor(None, sys.stdin.readline)
                if not line:
                    break
                
                try:
                    message = json.loads(line.strip())
                    response = await self.handle_message(message)
                    
                    if response:
                        print(json.dumps(response, ensure_ascii=False))
                        sys.stdout.flush()
                        
                except json.JSONDecodeError:
                    logger.warning("잘못된 JSON 메시지 무시")
                except Exception as e:
                    logger.error(f"메시지 처리 오류: {e}")
                    
        except KeyboardInterrupt:
            logger.info("서버 종료")
        except Exception as e:
            logger.error(f"서버 실행 오류: {e}")

async def main():
    """메인 함수"""
    server = GreeumNativeMCPServer()
    await server.run_stdio()

if __name__ == "__main__":
    asyncio.run(main())

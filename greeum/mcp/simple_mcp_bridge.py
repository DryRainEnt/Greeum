#!/usr/bin/env python3
"""
Greeum v2.0 Simple MCP Bridge
- 환경 독립적 MCP 연결
- Greeum v2.0 CLI 기반 동작
- 최소 의존성, 최대 안정성
"""

import json
import sys
import os
import asyncio
import logging
import subprocess
from typing import Dict, Any, List, Optional
from pathlib import Path

# 로깅 설정
logging.basicConfig(level=logging.INFO, stream=sys.stderr)
logger = logging.getLogger("simple_mcp_bridge")

class SimpleMCPBridge:
    """간단하고 안정적인 MCP 브리지"""
    
    def __init__(self):
        """초기화 - 최소한의 설정"""
        try:
            self.greeum_cli = self._find_greeum_cli()
        except Exception as e:
            logger.warning(f"Failed to find Greeum CLI: {e}")
            self.greeum_cli = "python3 -m greeum.cli"  # 안전한 기본값
        logger.info(f"Simple MCP Bridge initialized with CLI: {self.greeum_cli}")
        
    def _find_greeum_cli(self) -> str:
        """Greeum CLI 경로 자동 감지"""
        # 현재 디렉토리 기준
        current_dir = Path(__file__).parent.parent.parent
        
        # 방법 1: 직접 Python 모듈로 실행
        if (current_dir / "greeum" / "cli" / "__init__.py").exists():
            return f"python3 -m greeum.cli"
            
        # 방법 2: 설치된 greeum 명령어 사용
        try:
            subprocess.run(["greeum", "--version"], capture_output=True, check=True)
            return "greeum"
        except (subprocess.CalledProcessError, FileNotFoundError):
            pass
            
        # 방법 3: 직접 Python 실행
        return f"python3 {current_dir / 'greeum' / 'cli' / '__init__.py'}"
    
    def _run_greeum_command(self, command: List[str]) -> Dict[str, Any]:
        """Greeum CLI 명령어 실행"""
        try:
            full_command = self.greeum_cli.split() + command
            logger.info(f"Running command: {' '.join(full_command)}")
            
            # 보안: 허용된 명령어만 실행
            allowed_commands = ["memory", "add", "search", "stats", "--version", "--help"]
            for cmd_part in command:
                if cmd_part not in allowed_commands and not cmd_part.startswith(('-', '=')):
                    # 명령어 인젝션 방지: 안전한 텍스트만 허용
                    if not all(c.isalnum() or c in ' .-_가-힣ㄱ-ㅎㅏ-ㅣ' for c in cmd_part):
                        raise ValueError(f"Unsafe command detected: {cmd_part}")
            
            result = subprocess.run(
                full_command,
                capture_output=True,
                text=True,
                check=True,
                timeout=30  # 보안: 타임아웃 설정
            )
            
            if result.stdout:
                # JSON 응답인지 확인
                try:
                    return json.loads(result.stdout)
                except json.JSONDecodeError:
                    # 텍스트 응답을 JSON으로 래핑
                    return {"success": True, "output": result.stdout.strip()}
            else:
                return {"success": True, "output": "Command executed successfully"}
                
        except subprocess.CalledProcessError as e:
            logger.error(f"Command failed: {e}")
            return {
                "success": False, 
                "error": f"Command failed: {e.stderr or str(e)}"
            }
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            return {"success": False, "error": str(e)}
    
    def add_memory(self, content: str, importance: float = 0.5) -> Dict[str, Any]:
        """메모리 추가"""
        command = ["memory", "add", content, "--importance", str(importance)]
        return self._run_greeum_command(command)
    
    def search_memory(self, query: str, limit: int = 5) -> Dict[str, Any]:
        """메모리 검색"""
        command = ["memory", "search", query, "--count", str(limit)]
        return self._run_greeum_command(command)
    
    def get_memory_stats(self) -> Dict[str, Any]:
        """메모리 통계"""
        # CLI에 status 명령어가 없으므로 직접 구현
        try:
            import os
            from pathlib import Path
            
            # Greeum 데이터 디렉토리 확인
            data_dir = Path.home() / ".greeum"
            if not data_dir.exists():
                data_dir = Path("/Users/dryrain/DevRoom/Greeum/data")
            
            stats = {
                "data_directory": str(data_dir),
                "exists": data_dir.exists(),
                "files": []
            }
            
            if data_dir.exists():
                for file in data_dir.glob("*"):
                    if file.is_file():
                        stats["files"].append({
                            "name": file.name,
                            "size": file.stat().st_size,
                            "modified": file.stat().st_mtime
                        })
            
            return {"success": True, "stats": stats}
            
        except Exception as e:
            return {"success": False, "error": f"Failed to get stats: {str(e)}"}   

class SimpleMCPProtocol:
    """초간단 MCP 프로토콜"""
    
    def __init__(self):
        self.bridge = SimpleMCPBridge()
        
    async def handle_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """MCP 요청 처리"""
        try:
            method = request.get('method', '')
            params = request.get('params', {})
            request_id = request.get('id', 1)
            
            logger.info(f"Handling method: {method}")
            
            if method == 'initialize':
                return {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "result": {
                        "protocolVersion": "2024-11-05",
                        "capabilities": {
                            "tools": {},
                            "resources": {},
                            "prompts": {},
                            "logging": {}
                        },
                        "serverInfo": {
                            "name": "greeum-simple-bridge",
                            "version": "2.0.3"
                        }
                    }
                }
            
            elif method == 'tools/list':
                return {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "result": {
                        "tools": [
                            {
                                "name": "greeum_add_memory",
                                "description": "Add new memory to Greeum v2.0 long-term storage",
                                "inputSchema": {
                                    "type": "object",
                                    "properties": {
                                        "content": {"type": "string", "description": "Memory content to store"},
                                        "importance": {"type": "number", "default": 0.5, "description": "Importance score 0.0-1.0"}
                                    },
                                    "required": ["content"]
                                }
                            },
                            {
                                "name": "greeum_search_memory", 
                                "description": "Search memories in Greeum v2.0 using keywords or semantic similarity",
                                "inputSchema": {
                                    "type": "object", 
                                    "properties": {
                                        "query": {"type": "string", "description": "Search query or keywords"},
                                        "limit": {"type": "number", "default": 5, "description": "Maximum number of results"}
                                    },
                                    "required": ["query"]
                                }
                            },
                            {
                                "name": "greeum_memory_stats",
                                "description": "Get Greeum v2.0 memory system statistics and status", 
                                "inputSchema": {
                                    "type": "object",
                                    "properties": {}
                                }
                            }
                        ]
                    }
                }
                
            elif method == 'tools/call':
                tool_name = params.get('name', '')
                arguments = params.get('arguments', {})
                
                logger.info(f"Calling tool: {tool_name} with args: {arguments}")
                
                if tool_name == 'greeum_add_memory':
                    result = self.bridge.add_memory(
                        content=arguments.get('content', ''),
                        importance=arguments.get('importance', 0.5)
                    )
                elif tool_name == 'greeum_search_memory':
                    result = self.bridge.search_memory(
                        query=arguments.get('query', ''),
                        limit=arguments.get('limit', 5)
                    )
                elif tool_name == 'greeum_memory_stats':
                    result = self.bridge.get_memory_stats()
                else:
                    return {
                        "jsonrpc": "2.0",
                        "id": request_id,
                        "error": {
                            "code": -32601,
                            "message": f"Unknown tool: {tool_name}"
                        }
                    }
                
                return {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "result": {
                        "content": [{
                            "type": "text", 
                            "text": json.dumps(result, indent=2, ensure_ascii=False)
                        }]
                    }
                }
                
            # 지원하지 않는 메서드
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "error": {
                    "code": -32601,
                    "message": f"Method not found: {method}"
                }
            }
            
        except Exception as e:
            logger.error(f"Request handling failed: {e}")
            return {
                "jsonrpc": "2.0", 
                "id": request.get('id', 1),
                "error": {
                    "code": -32603,
                    "message": f"Internal error: {str(e)}"
                }
            }

async def main():
    """메인 서버 실행"""
    try:
        protocol = SimpleMCPProtocol()
        logger.info("Simple Greeum MCP Bridge started")
        
        # STDIO 모드에서 JSON-RPC 메시지 처리
        while True:
            try:
                line = sys.stdin.readline()
                if not line:
                    break
                    
                line = line.strip()
                if not line:
                    continue
                    
                # JSON-RPC 요청 파싱
                request = json.loads(line)
                response = await protocol.handle_request(request)
                
                # 응답 전송
                print(json.dumps(response), flush=True)
                
            except json.JSONDecodeError as e:
                logger.error(f"Invalid JSON received: {e}")
                error_response = {
                    "jsonrpc": "2.0",
                    "id": None,
                    "error": {"code": -32700, "message": "Parse error"}
                }
                print(json.dumps(error_response), flush=True)
                
            except KeyboardInterrupt:
                logger.info("Server interrupted by user")
                break
                
            except Exception as e:
                logger.error(f"Unexpected error: {e}")
                
    except Exception as e:
        logger.error(f"Server startup failed: {e}")
        sys.exit(1)
    finally:
        logger.info("Simple Greeum MCP Bridge stopped")

if __name__ == "__main__":
    # Python 버전 확인
    if sys.version_info < (3, 6):
        print("Error: Python 3.6+ required", file=sys.stderr)
        sys.exit(1)
        
    # 비동기 실행
    try:
        asyncio.run(main())
    except AttributeError:
        # Python 3.6 호환성
        loop = asyncio.get_event_loop()
        loop.run_until_complete(main())
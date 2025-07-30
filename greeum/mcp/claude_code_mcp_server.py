#!/usr/bin/env python3
"""
Claude Code 호환 MCP 서버
- Claude Code의 MCP 프로토콜 규격에 정확히 맞춤
- 도구 인식 문제 해결을 위한 완전 호환 버전
"""

import asyncio
import json
import sys
import logging
from typing import Dict, Any, List, Optional
import subprocess
import os
from pathlib import Path

# 로깅 설정 (stderr로만)
logging.basicConfig(level=logging.INFO, stream=sys.stderr, format='%(levelname)s:%(name)s:%(message)s')
logger = logging.getLogger("claude_code_mcp")

class ClaudeCodeMCPServer:
    """Claude Code 완전 호환 MCP 서버"""
    
    def __init__(self):
        """초기화"""
        self.server_info = {
            "name": "greeum",
            "version": "2.0.2"
        }
        self.protocol_version = "2024-11-05"
        self.capabilities = {
            "tools": {},
            "resources": {},
            "prompts": {},
            "logging": {}
        }
        
        # Greeum CLI 경로 설정
        self.greeum_cli = self._find_greeum_cli()
        logger.info(f"Claude Code MCP Server initialized with CLI: {self.greeum_cli}")
        
    def _find_greeum_cli(self) -> str:
        """Greeum CLI 경로 자동 감지"""
        current_dir = Path(__file__).parent.parent.parent
        
        # 방법 1: Python 모듈 실행
        if (current_dir / "greeum" / "cli" / "__init__.py").exists():
            return f"python3 -m greeum.cli"
            
        # 방법 2: 설치된 명령어
        try:
            subprocess.run(["greeum", "--version"], capture_output=True, check=True)
            return "greeum"
        except (subprocess.CalledProcessError, FileNotFoundError):
            pass
            
        # 기본값
        return f"python3 -m greeum.cli"
    
    def _run_cli_command(self, command: List[str]) -> Dict[str, Any]:
        """CLI 명령어 실행"""
        try:
            full_command = self.greeum_cli.split() + command
            logger.info(f"Running: {' '.join(full_command)}")
            
            result = subprocess.run(
                full_command,
                capture_output=True,
                text=True,
                check=True
            )
            
            return {"success": True, "output": result.stdout.strip()}
                
        except subprocess.CalledProcessError as e:
            logger.error(f"CLI command failed: {e}")
            return {"success": False, "error": f"Command failed: {e.stderr or str(e)}"}
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            return {"success": False, "error": str(e)}

    async def handle_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """MCP 요청 처리 (Claude Code 규격 준수)"""
        try:
            method = request.get('method', '')
            params = request.get('params', {})
            request_id = request.get('id', 1)
            
            logger.info(f"Handling method: {method}")
            
            # 1. Initialize
            if method == 'initialize':
                return {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "result": {
                        "protocolVersion": self.protocol_version,
                        "capabilities": self.capabilities,
                        "serverInfo": self.server_info
                    }
                }
            
            # 2. Tools list
            elif method == 'tools/list':
                return {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "result": {
                        "tools": [
                            {
                                "name": "add_memory",
                                "description": "Add new memory to Greeum v2.0 long-term storage",
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
                                            "default": 0.5,
                                            "minimum": 0.0,
                                            "maximum": 1.0
                                        }
                                    },
                                    "required": ["content"]
                                }
                            },
                            {
                                "name": "search_memory",
                                "description": "Search memories using keywords or semantic similarity",
                                "inputSchema": {
                                    "type": "object",
                                    "properties": {
                                        "query": {
                                            "type": "string",
                                            "description": "Search query or keywords"
                                        },
                                        "limit": {
                                            "type": "integer",
                                            "description": "Maximum number of results",
                                            "default": 5,
                                            "minimum": 1,
                                            "maximum": 50
                                        }
                                    },
                                    "required": ["query"]
                                }
                            },
                            {
                                "name": "get_memory_stats",
                                "description": "Get Greeum memory system statistics",
                                "inputSchema": {
                                    "type": "object",
                                    "properties": {}
                                }
                            },
                            # LTM 전용 도구들
                            {
                                "name": "ltm_analyze",
                                "description": "Analyze long-term memory patterns and trends",
                                "inputSchema": {
                                    "type": "object",
                                    "properties": {
                                        "trends": {"type": "boolean", "description": "Enable trend analysis", "default": True},
                                        "period": {"type": "string", "description": "Analysis period (e.g., 6m, 1y)", "default": "6m"},
                                        "output": {"type": "string", "description": "Output format", "enum": ["text", "json"], "default": "text"}
                                    }
                                }
                            },
                            {
                                "name": "ltm_verify",
                                "description": "Verify blockchain-like LTM integrity",
                                "inputSchema": {
                                    "type": "object",
                                    "properties": {
                                        "repair": {"type": "boolean", "description": "Attempt to repair issues", "default": False}
                                    }
                                }
                            },
                            {
                                "name": "ltm_export",
                                "description": "Export LTM data in various formats",
                                "inputSchema": {
                                    "type": "object",
                                    "properties": {
                                        "format": {"type": "string", "description": "Export format", "enum": ["json", "blockchain", "csv"], "default": "json"},
                                        "limit": {"type": "integer", "description": "Limit number of blocks", "minimum": 1, "maximum": 1000}
                                    }
                                }
                            },
                            # STM 전용 도구들
                            {
                                "name": "stm_add",
                                "description": "Add content to short-term memory with TTL",
                                "inputSchema": {
                                    "type": "object",
                                    "properties": {
                                        "content": {"type": "string", "description": "Content to add to STM"},
                                        "ttl": {"type": "string", "description": "Time to live (e.g., 1h, 30m, 2d)", "default": "1h"},
                                        "importance": {"type": "number", "description": "Importance score", "default": 0.3, "minimum": 0.0, "maximum": 1.0}
                                    },
                                    "required": ["content"]
                                }
                            },
                            {
                                "name": "stm_promote",
                                "description": "Promote important STM entries to LTM",
                                "inputSchema": {
                                    "type": "object",
                                    "properties": {
                                        "threshold": {"type": "number", "description": "Importance threshold", "default": 0.8, "minimum": 0.0, "maximum": 1.0},
                                        "dry_run": {"type": "boolean", "description": "Show what would be promoted", "default": False}
                                    }
                                }
                            },
                            {
                                "name": "stm_cleanup",
                                "description": "Clean up short-term memory entries",
                                "inputSchema": {
                                    "type": "object",
                                    "properties": {
                                        "smart": {"type": "boolean", "description": "Use intelligent cleanup", "default": False},
                                        "expired": {"type": "boolean", "description": "Remove only expired entries", "default": False},
                                        "threshold": {"type": "number", "description": "Remove below this importance", "default": 0.2, "minimum": 0.0, "maximum": 1.0}
                                    }
                                }
                            }
                        ]
                    }
                }
                
            # 3. Tools call
            elif method == 'tools/call':
                tool_name = params.get('name', '')
                arguments = params.get('arguments', {})
                
                logger.info(f"Calling tool: {tool_name} with args: {arguments}")
                
                # add_memory 도구
                if tool_name == 'add_memory':
                    content = arguments.get('content', '')
                    importance = arguments.get('importance', 0.5)
                    
                    command = ["memory", "add", content, "--importance", str(importance)]
                    result = self._run_cli_command(command)
                    
                    if result["success"]:
                        return {
                            "jsonrpc": "2.0",
                            "id": request_id,
                            "result": {
                                "content": [
                                    {
                                        "type": "text",
                                        "text": f"✅ Memory added successfully: {result['output']}"
                                    }
                                ]
                            }
                        }
                    else:
                        return {
                            "jsonrpc": "2.0",
                            "id": request_id,
                            "error": {
                                "code": -32603,
                                "message": f"Failed to add memory: {result['error']}"
                            }
                        }
                
                # search_memory 도구
                elif tool_name == 'search_memory':
                    query = arguments.get('query', '')
                    limit = arguments.get('limit', 5)
                    
                    command = ["memory", "search", query, "--count", str(limit)]
                    result = self._run_cli_command(command)
                    
                    if result["success"]:
                        return {
                            "jsonrpc": "2.0",
                            "id": request_id,
                            "result": {
                                "content": [
                                    {
                                        "type": "text",
                                        "text": f"🔍 Search results:\n{result['output']}"
                                    }
                                ]
                            }
                        }
                    else:
                        return {
                            "jsonrpc": "2.0",
                            "id": request_id,
                            "error": {
                                "code": -32603,
                                "message": f"Failed to search memory: {result['error']}"
                            }
                        }
                
                # get_memory_stats 도구
                elif tool_name == 'get_memory_stats':
                    try:
                        # 메모리 통계 직접 수집
                        data_dir = Path.home() / ".greeum"
                        
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
                                        "size": file.stat().st_size
                                    })
                        
                        return {
                            "jsonrpc": "2.0",
                            "id": request_id,
                            "result": {
                                "content": [
                                    {
                                        "type": "text",
                                        "text": f"📊 Memory Statistics:\n{json.dumps(stats, indent=2)}"
                                    }
                                ]
                            }
                        }
                        
                    except Exception as e:
                        return {
                            "jsonrpc": "2.0",
                            "id": request_id,
                            "error": {
                                "code": -32603,
                                "message": f"Failed to get stats: {str(e)}"
                            }
                        }
                
                # LTM 도구들
                elif tool_name == 'ltm_analyze':
                    trends = arguments.get('trends', True)
                    period = arguments.get('period', '6m')
                    output = arguments.get('output', 'text')
                    
                    command = ["ltm", "analyze", "--period", period, "--output", output]
                    if trends:
                        command.append("--trends")
                    
                    result = self._run_cli_command(command)
                    
                    if result["success"]:
                        return {
                            "jsonrpc": "2.0",
                            "id": request_id,
                            "result": {
                                "content": [{"type": "text", "text": f"📊 LTM Analysis:\n{result['output']}"}]
                            }
                        }
                    else:
                        return {
                            "jsonrpc": "2.0",
                            "id": request_id,
                            "error": {"code": -32603, "message": f"LTM analysis failed: {result['error']}"}
                        }
                
                elif tool_name == 'ltm_verify':
                    repair = arguments.get('repair', False)
                    
                    command = ["ltm", "verify"]
                    if repair:
                        command.append("--repair")
                    
                    result = self._run_cli_command(command)
                    
                    if result["success"]:
                        return {
                            "jsonrpc": "2.0",
                            "id": request_id,
                            "result": {
                                "content": [{"type": "text", "text": f"🔍 LTM Verification:\n{result['output']}"}]
                            }
                        }
                    else:
                        return {
                            "jsonrpc": "2.0",
                            "id": request_id,
                            "error": {"code": -32603, "message": f"LTM verification failed: {result['error']}"}
                        }
                
                elif tool_name == 'ltm_export':
                    format_type = arguments.get('format', 'json')
                    limit = arguments.get('limit')
                    
                    command = ["ltm", "export", "--format", format_type]
                    if limit:
                        command.extend(["--limit", str(limit)])
                    
                    result = self._run_cli_command(command)
                    
                    if result["success"]:
                        return {
                            "jsonrpc": "2.0",
                            "id": request_id,
                            "result": {
                                "content": [{"type": "text", "text": f"📤 LTM Export:\n{result['output']}"}]
                            }
                        }
                    else:
                        return {
                            "jsonrpc": "2.0",
                            "id": request_id,
                            "error": {"code": -32603, "message": f"LTM export failed: {result['error']}"}
                        }
                
                # STM 도구들
                elif tool_name == 'stm_add':
                    content = arguments.get('content', '')
                    ttl = arguments.get('ttl', '1h')
                    importance = arguments.get('importance', 0.3)
                    
                    command = ["stm", "add", content, "--ttl", ttl, "--importance", str(importance)]
                    result = self._run_cli_command(command)
                    
                    if result["success"]:
                        return {
                            "jsonrpc": "2.0",
                            "id": request_id,
                            "result": {
                                "content": [{"type": "text", "text": f"🧠 STM Add:\n{result['output']}"}]
                            }
                        }
                    else:
                        return {
                            "jsonrpc": "2.0",
                            "id": request_id,
                            "error": {"code": -32603, "message": f"STM add failed: {result['error']}"}
                        }
                
                elif tool_name == 'stm_promote':
                    threshold = arguments.get('threshold', 0.8)
                    dry_run = arguments.get('dry_run', False)
                    
                    command = ["stm", "promote", "--threshold", str(threshold)]
                    if dry_run:
                        command.append("--dry-run")
                    
                    result = self._run_cli_command(command)
                    
                    if result["success"]:
                        return {
                            "jsonrpc": "2.0",
                            "id": request_id,
                            "result": {
                                "content": [{"type": "text", "text": f"🔝 STM Promote:\n{result['output']}"}]
                            }
                        }
                    else:
                        return {
                            "jsonrpc": "2.0",
                            "id": request_id,
                            "error": {"code": -32603, "message": f"STM promote failed: {result['error']}"}
                        }
                
                elif tool_name == 'stm_cleanup':
                    smart = arguments.get('smart', False)
                    expired = arguments.get('expired', False)
                    threshold = arguments.get('threshold', 0.2)
                    
                    command = ["stm", "cleanup", "--threshold", str(threshold)]
                    if smart:
                        command.append("--smart")
                    if expired:
                        command.append("--expired")
                    
                    result = self._run_cli_command(command)
                    
                    if result["success"]:
                        return {
                            "jsonrpc": "2.0",
                            "id": request_id,
                            "result": {
                                "content": [{"type": "text", "text": f"🧹 STM Cleanup:\n{result['output']}"}]
                            }
                        }
                    else:
                        return {
                            "jsonrpc": "2.0",
                            "id": request_id,
                            "error": {"code": -32603, "message": f"STM cleanup failed: {result['error']}"}
                        }
                
                # 알 수 없는 도구
                else:
                    return {
                        "jsonrpc": "2.0",
                        "id": request_id,
                        "error": {
                            "code": -32601,
                            "message": f"Unknown tool: {tool_name}"
                        }
                    }
            
            # 4. Notifications (처리하지 않음)
            elif method == 'notifications/initialized':
                # 알림은 응답하지 않음
                return None
                
            # 5. 지원하지 않는 메서드
            else:
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
    """메인 서버 루프"""
    try:
        server = ClaudeCodeMCPServer()
        logger.info("Claude Code compatible MCP server started")
        
        # STDIO로 JSON-RPC 메시지 처리
        while True:
            try:
                line = sys.stdin.readline()
                if not line:
                    break
                    
                line = line.strip()
                if not line:
                    continue
                    
                # JSON 파싱
                request = json.loads(line)
                response = await server.handle_request(request)
                
                # 응답 전송 (None이 아닌 경우에만)
                if response is not None:
                    print(json.dumps(response), flush=True)
                
            except json.JSONDecodeError as e:
                logger.error(f"Invalid JSON: {e}")
                error_response = {
                    "jsonrpc": "2.0",
                    "id": None,
                    "error": {"code": -32700, "message": "Parse error"}
                }
                print(json.dumps(error_response), flush=True)
                
            except KeyboardInterrupt:
                logger.info("Server interrupted")
                break
                
            except Exception as e:
                logger.error(f"Unexpected error: {e}")
                
    except Exception as e:
        logger.error(f"Server startup failed: {e}")
        sys.exit(1)
    finally:
        logger.info("Claude Code MCP server stopped")

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
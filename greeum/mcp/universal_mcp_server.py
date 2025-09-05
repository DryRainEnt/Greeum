#!/usr/bin/env python3
"""
Greeum v2.0 Universal MCP Server
- 환경 독립적 (어떤 Python 환경에서도 동작)
- 최소 의존성 (내장 라이브러리만 사용)  
- 자체 완비형 (단일 파일로 모든 기능)
- 강력한 오류 처리
"""

import json
import sys
import os
import asyncio
import logging
from typing import Dict, Any, List, Optional
from pathlib import Path
import subprocess
import sqlite3
from datetime import datetime

# 로깅 설정
logging.basicConfig(level=logging.INFO, stream=sys.stderr)
logger = logging.getLogger("greeum_universal")

class UniversalGreeumMCP:
    """환경 독립적 Greeum MCP 서버"""
    
    def __init__(self, data_dir: Optional[str] = None):
        """
        초기화 - 어떤 환경에서도 안전하게 작동
        """
        # 데이터 디렉토리 설정 (환경별 자동 감지)
        if data_dir is None:
            if os.name == 'nt':  # Windows
                data_dir = os.path.join(os.environ.get('APPDATA', ''), 'Greeum')
            else:  # Unix/Linux/macOS
                data_dir = os.path.expanduser('~/.greeum')
        
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.db_path = self.data_dir / 'universal_memory.db'
        
        logger.info(f"Universal Greeum MCP Server - Data: {self.data_dir}")
        
        # 데이터베이스 초기화
        self._init_database()
        
    def _init_database(self):
        """SQLite 데이터베이스 초기화 (내장 라이브러리만 사용)"""
        try:
            with sqlite3.connect(str(self.db_path)) as conn:
                conn.execute('''
                    CREATE TABLE IF NOT EXISTS memories (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        timestamp TEXT NOT NULL,
                        content TEXT NOT NULL,
                        keywords TEXT,
                        tags TEXT,
                        importance REAL DEFAULT 0.5,
                        created_at TEXT DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                conn.commit()
                logger.info("Database initialized successfully")
        except Exception as e:
            logger.error(f"Database initialization failed: {e}")
            
    def add_memory(self, content: str, keywords: List[str] = None, 
                   tags: List[str] = None, importance: float = 0.5) -> Dict[str, Any]:
        """메모리 추가 - 안전하고 간단한 구현"""
        try:
            timestamp = datetime.now().isoformat()
            keywords_str = ','.join(keywords or [])
            tags_str = ','.join(tags or [])
            
            with sqlite3.connect(str(self.db_path)) as conn:
                cursor = conn.execute('''
                    INSERT INTO memories (timestamp, content, keywords, tags, importance)
                    VALUES (?, ?, ?, ?, ?)
                ''', (timestamp, content, keywords_str, tags_str, importance))
                
                memory_id = cursor.lastrowid
                conn.commit()
                
                logger.info(f"Memory added: ID={memory_id}")
                return {
                    "success": True,
                    "id": memory_id,
                    "timestamp": timestamp,
                    "content": content[:100] + "..." if len(content) > 100 else content
                }
                
        except Exception as e:
            logger.error(f"Add memory failed: {e}")
            return {"success": False, "error": str(e)}
            
    def search_memory(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """메모리 검색 - 키워드 기반 간단 검색"""
        try:
            with sqlite3.connect(str(self.db_path)) as conn:
                conn.row_factory = sqlite3.Row
                
                # 간단한 LIKE 검색 (어떤 환경에서도 동작)
                cursor = conn.execute('''
                    SELECT * FROM memories 
                    WHERE content LIKE ? OR keywords LIKE ? OR tags LIKE ?
                    ORDER BY created_at DESC
                    LIMIT ?
                ''', (f'%{query}%', f'%{query}%', f'%{query}%', limit))
                
                results = []
                for row in cursor.fetchall():
                    results.append({
                        "id": row["id"],
                        "timestamp": row["timestamp"],
                        "content": row["content"],
                        "keywords": row["keywords"].split(',') if row["keywords"] else [],
                        "tags": row["tags"].split(',') if row["tags"] else [],
                        "importance": row["importance"]
                    })
                
                logger.info(f"Search '{query}' found {len(results)} results")
                return results
                
        except Exception as e:
            logger.error(f"Search memory failed: {e}")
            return []
            
    def get_memory_stats(self) -> Dict[str, Any]:
        """메모리 통계 - 시스템 상태 확인"""
        try:
            with sqlite3.connect(str(self.db_path)) as conn:
                cursor = conn.execute('SELECT COUNT(*) as total FROM memories')
                total = cursor.fetchone()[0]
                
                cursor = conn.execute('''
                    SELECT AVG(importance) as avg_importance FROM memories
                ''')
                avg_importance = cursor.fetchone()[0] or 0.0
                
                return {
                    "success": True,
                    "total_memories": total,
                    "average_importance": round(avg_importance, 2),
                    "database_path": str(self.db_path),
                    "data_directory": str(self.data_dir)
                }
                
        except Exception as e:
            logger.error(f"Get stats failed: {e}")
            return {"success": False, "error": str(e)}

class SimpleMCPProtocol:
    """초간단 MCP 프로토콜 구현 (내장 라이브러리만 사용)"""
    
    def __init__(self, greeum: UniversalGreeumMCP):
        self.greeum = greeum
        
    def handle_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """MCP 요청 처리"""
        try:
            method = request.get('method', '')
            params = request.get('params', {})
            request_id = request.get('id', 1)
            
            if method == 'tools/list':
                return {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "result": {
                        "tools": [
                            {
                                "name": "add_memory",
                                "description": "Add new memory to Greeum",
                                "inputSchema": {
                                    "type": "object",
                                    "properties": {
                                        "content": {"type": "string"},
                                        "importance": {"type": "number", "default": 0.5}
                                    },
                                    "required": ["content"]
                                }
                            },
                            {
                                "name": "search_memory", 
                                "description": "Search memories in Greeum",
                                "inputSchema": {
                                    "type": "object", 
                                    "properties": {
                                        "query": {"type": "string"},
                                        "limit": {"type": "number", "default": 5}
                                    },
                                    "required": ["query"]
                                }
                            },
                            {
                                "name": "memory_stats",
                                "description": "Get Greeum memory statistics", 
                                "inputSchema": {"type": "object"}
                            }
                        ]
                    }
                }
                
            elif method == 'tools/call':
                tool_name = params.get('name', '')
                arguments = params.get('arguments', {})
                
                if tool_name == 'add_memory':
                    result = self.greeum.add_memory(
                        content=arguments.get('content', ''),
                        importance=arguments.get('importance', 0.5)
                    )
                    return {
                        "jsonrpc": "2.0",
                        "id": request_id,
                        "result": {
                            "content": [{"type": "text", "text": json.dumps(result, indent=2)}]
                        }
                    }
                    
                elif tool_name == 'search_memory':
                    results = self.greeum.search_memory(
                        query=arguments.get('query', ''),
                        limit=arguments.get('limit', 5)
                    )
                    return {
                        "jsonrpc": "2.0", 
                        "id": request_id,
                        "result": {
                            "content": [{"type": "text", "text": json.dumps(results, indent=2)}]
                        }
                    }
                    
                elif tool_name == 'memory_stats':
                    stats = self.greeum.get_memory_stats()
                    return {
                        "jsonrpc": "2.0",
                        "id": request_id, 
                        "result": {
                            "content": [{"type": "text", "text": json.dumps(stats, indent=2)}]
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
        # Greeum 초기화
        greeum = UniversalGreeumMCP()
        protocol = SimpleMCPProtocol(greeum)
        
        logger.info("Universal Greeum MCP Server started")
        
        # STDIO 모드에서 JSON-RPC 메시지 처리
        while True:
            try:
                line = sys.stdin.readline()
                if not line:
                    break
                    
                # JSON-RPC 요청 파싱
                request = json.loads(line.strip())
                response = protocol.handle_request(request)
                
                # 응답 전송
                print(json.dumps(response))
                sys.stdout.flush()
                
            except json.JSONDecodeError as e:
                logger.error(f"Invalid JSON received: {e}")
                error_response = {
                    "jsonrpc": "2.0",
                    "id": None,
                    "error": {"code": -32700, "message": "Parse error"}
                }
                print(json.dumps(error_response))
                sys.stdout.flush()
                
            except KeyboardInterrupt:
                logger.info("Server interrupted by user")
                break
                
            except Exception as e:
                logger.error(f"Unexpected error: {e}")
                
    except Exception as e:
        logger.error(f"Server startup failed: {e}")
        sys.exit(1)
    finally:
        logger.info("Universal Greeum MCP Server stopped")

if __name__ == "__main__":
    # Python 버전 확인 (3.6+ 필요)
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
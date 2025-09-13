#!/usr/bin/env python3
"""
Greeum MCP Server Core
순수한 서버 로직만 담당하는 코어 모듈

🎯 설계 원칙:
- 순수한 서버 로직만 포함
- CLI 호출과 완전 분리
- FastMCP 프레임워크 기반
- 재사용 가능한 서버 컴포넌트

🔧 책임:
- Greeum 컴포넌트 초기화
- MCP 도구 정의 및 등록
- 서버 실행 로직
"""

import logging
import sys
from typing import Dict, Any, List, Optional

# FastMCP import
try:
    from mcp.server.fastmcp import FastMCP
except ImportError:
    print("ERROR: FastMCP not found. Please install: pip install mcp>=1.0.0", file=sys.stderr)
    sys.exit(1)

# Greeum core imports
try:
    from greeum.core.block_manager import BlockManager
    from greeum.core import DatabaseManager  # Use factory pattern from __init__.py
    from greeum.core.stm_manager import STMManager
    from greeum.core.duplicate_detector import DuplicateDetector
    from greeum.core.quality_validator import QualityValidator
    from greeum.core.usage_analytics import UsageAnalytics
    GREEUM_AVAILABLE = True
except ImportError:
    GREEUM_AVAILABLE = False

# 로깅 설정
logger = logging.getLogger("greeum_server_core")

class GreeumMCPServer:
    """Greeum MCP 서버 코어 클래스"""
    
    def __init__(self):
        self.app = FastMCP("Greeum Memory System")
        self._components = None
        self._initialized = False
        
    def _get_version(self) -> str:
        """중앙화된 버전 참조"""
        try:
            from greeum import __version__
            return __version__
        except ImportError:
            return "unknown"
        
    async def initialize(self) -> None:
        """서버 컴포넌트 초기화"""
        if self._initialized:
            return
            
        if not GREEUM_AVAILABLE:
            raise RuntimeError("Greeum components not available")
            
        try:
            # Greeum 컴포넌트 초기화
            db_manager = DatabaseManager()
            block_manager = BlockManager(db_manager)
            stm_manager = STMManager(db_manager)
            duplicate_detector = DuplicateDetector(db_manager)
            quality_validator = QualityValidator()
            usage_analytics = UsageAnalytics(db_manager)
            
            self._components = {
                'db_manager': db_manager,
                'block_manager': block_manager,
                'stm_manager': stm_manager,
                'duplicate_detector': duplicate_detector,
                'quality_validator': quality_validator,
                'usage_analytics': usage_analytics
            }
            
            # MCP 도구 등록
            self._register_tools()
            
            self._initialized = True
            logger.info("Greeum MCP server components initialized")
            
        except Exception as e:
            logger.error(f"Failed to initialize server components: {e}")
            raise
    
    def _register_tools(self) -> None:
        """MCP 도구들을 서버에 등록"""
        
        @self.app.tool()
        def add_memory(content: str, importance: float = 0.5) -> str:
            """[MEMORY] Add important permanent memories to long-term storage."""
            return self._handle_add_memory(content, importance)
            
        @self.app.tool()
        def search_memory(query: str, limit: int = 5) -> str:
            """🔍 Search existing memories using keywords or semantic similarity."""
            return self._handle_search_memory(query, limit)
            
        @self.app.tool()
        def get_memory_stats() -> str:
            """📊 Get current memory system statistics and health status."""
            return self._handle_get_stats()
            
        @self.app.tool()
        def usage_analytics(days: int = 7, report_type: str = "usage") -> str:
            """📊 Get comprehensive usage analytics and insights."""
            return self._handle_usage_analytics(days, report_type)
            
        logger.info("All MCP tools registered: add_memory, search_memory, get_memory_stats, usage_analytics")
    
    def _handle_add_memory(self, content: str, importance: float) -> str:
        """add_memory 도구 핸들러"""
        try:
            if not self._components:
                return "ERROR: Server not properly initialized"
            
            # 중복 검사
            duplicate_check = self._components['duplicate_detector'].check_duplicate(content)
            if duplicate_check["is_duplicate"]:
                similarity = duplicate_check["similarity_score"]
                return f"""WARNING: Potential Duplicate Memory Detected

**Similarity**: {similarity:.1%} with existing memory
**Similar Memory**: Block #{duplicate_check['similar_block_index']}

Please search existing memories first or provide more specific content."""
            
            # 품질 검증
            quality_result = self._components['quality_validator'].validate_memory_quality(content, importance)
            
            # 메모리 추가
            block_data = self._add_memory_direct(content, importance)
            
            # 사용 통계 로깅
            self._components['usage_analytics'].log_quality_metrics(
                len(content), quality_result['quality_score'], quality_result['quality_level'],
                importance, importance, False, duplicate_check["similarity_score"], 
                len(quality_result['suggestions'])
            )
            
            # 성공 응답
            quality_feedback = f"""
**Quality Score**: {quality_result['quality_score']:.1%} ({quality_result['quality_level']})
**Adjusted Importance**: {importance:.2f} (original: {importance:.2f})"""
            
            suggestions_text = ""
            if quality_result['suggestions']:
                suggestions_text = f"\n\n**Quality Suggestions**:\n" + "\n".join(f"• {s}" for s in quality_result['suggestions'][:2])
            
            return f"""SUCCESS: Memory Successfully Added!

**Block Index**: #{block_data['block_index']}
**Storage**: Permanent (Long-term Memory)
**Duplicate Check**: PASSED{quality_feedback}{suggestions_text}"""
        
        except Exception as e:
            logger.error(f"add_memory failed: {e}")
            return f"ERROR: Failed to add memory: {str(e)}"
    
    def _handle_search_memory(self, query: str, limit: int) -> str:
        """search_memory 도구 핸들러"""
        try:
            if not self._components:
                return "ERROR: Server not properly initialized"
            
            results = self._search_memory_direct(query, limit)
            
            # 사용 통계 로깅
            self._components['usage_analytics'].log_event(
                "tool_usage", "search_memory",
                {"query_length": len(query), "results_found": len(results), "limit_requested": limit},
                0, True
            )
            
            if results:
                result_text = f"Found {len(results)} memories:\n"
                for i, memory in enumerate(results, 1):
                    timestamp = memory.get('timestamp', 'Unknown')
                    content = memory.get('context', '')[:100] + ('...' if len(memory.get('context', '')) > 100 else '')
                    result_text += f"{i}. [{timestamp}] {content}\n"
                return result_text
            else:
                return f"No memories found for query: '{query}'"
        
        except Exception as e:
            logger.error(f"search_memory failed: {e}")
            return f"ERROR: Search failed: {str(e)}"
    
    def _handle_get_stats(self) -> str:
        """get_memory_stats 도구 핸들러"""
        try:
            if not self._components:
                return "ERROR: Server not properly initialized"
            
            db_manager = self._components['db_manager']
            
            # 기본 통계
            total_blocks = db_manager.count_blocks()
            recent_blocks = db_manager.get_recent_blocks(limit=10)
            
            # STM 통계
            stm_stats = self._components['stm_manager'].get_stats()
            
            return f"""**Greeum Memory Statistics**

**Long-term Memory**:
• Total Blocks: {total_blocks}
• Recent Entries: {len(recent_blocks)}

**Short-term Memory**:
• Active Slots: {stm_stats.get('active_count', 0)}
• Available Slots: {stm_stats.get('available_slots', 0)}

**System Status**: Operational
**Version**: {self._get_version()} (Separated Architecture)"""
        
        except Exception as e:
            logger.error(f"get_memory_stats failed: {e}")
            return f"ERROR: Stats retrieval failed: {str(e)}"
    
    def _handle_usage_analytics(self, days: int, report_type: str) -> str:
        """usage_analytics 도구 핸들러"""
        try:
            if not self._components:
                return "ERROR: Server not properly initialized"
            
            analytics = self._components['usage_analytics'].get_usage_report(days=days, report_type=report_type)
            
            return f"""**Usage Analytics Report** ({days} days)

**Activity Summary**:
• Total Operations: {analytics.get('total_operations', 0)}
• Memory Additions: {analytics.get('add_operations', 0)}
• Search Operations: {analytics.get('search_operations', 0)}

**Quality Metrics**:
• Average Quality Score: {analytics.get('avg_quality_score', 0):.1%}
• High Quality Rate: {analytics.get('high_quality_rate', 0):.1%}

**Performance**:
• Average Response Time: {analytics.get('avg_response_time', 0):.1f}ms
• Success Rate: {analytics.get('success_rate', 0):.1%}

**Report Type**: {report_type.title()}
**Generated**: Separated Architecture v{self._get_version()}"""
        
        except Exception as e:
            logger.error(f"usage_analytics failed: {e}")
            return f"ERROR: Analytics failed: {str(e)}"
    
    def _add_memory_direct(self, content: str, importance: float) -> Dict[str, Any]:
        """직접 메모리 추가 (기존 로직 재사용)"""
        from greeum.text_utils import process_user_input
        from datetime import datetime
        import json
        import hashlib
        
        db_manager = self._components['db_manager']
        
        # 기존 로직 그대로 사용
        result = process_user_input(content)
        result["importance"] = importance
        
        timestamp = datetime.now().isoformat()
        result["timestamp"] = timestamp
        
        # 블록 인덱스 생성
        last_block_info = db_manager.get_last_block_info()
        if last_block_info is None:
            last_block_info = {"block_index": -1}
        block_index = last_block_info.get("block_index", -1) + 1
        
        # 이전 해시
        prev_hash = ""
        if block_index > 0:
            prev_block = db_manager.get_block(block_index - 1)
            if prev_block:
                prev_hash = prev_block.get("hash", "")
        
        # 해시 계산
        hash_data = {
            "block_index": block_index,
            "timestamp": timestamp,
            "context": content,
            "prev_hash": prev_hash
        }
        hash_str = json.dumps(hash_data, sort_keys=True)
        hash_value = hashlib.sha256(hash_str.encode()).hexdigest()
        
        # 최종 블록 데이터
        block_data = {
            "block_index": block_index,
            "timestamp": timestamp,
            "context": content,
            "keywords": result.get("keywords", []),
            "tags": result.get("tags", []),
            "embedding": result.get("embedding", []),
            "importance": result.get("importance", 0.5),
            "hash": hash_value,
            "prev_hash": prev_hash
        }
        
        # 데이터베이스에 추가
        db_manager.add_block(block_data)
        
        return block_data
    
    def _search_memory_direct(self, query: str, limit: int) -> List[Dict[str, Any]]:
        """직접 메모리 검색 (기존 로직 재사용)"""
        from greeum.embedding_models import get_embedding
        
        db_manager = self._components['db_manager']
        
        try:
            # 임베딩 기반 검색
            embedding = get_embedding(query)
            blocks = db_manager.search_blocks_by_embedding(embedding, top_k=limit)
            
            return blocks if blocks else []
        except Exception as e:
            logger.warning(f"Embedding search failed: {e}, falling back to keyword search")
            # 키워드 검색 폴백
            blocks = db_manager.search_by_keyword(query, limit=limit)
            return blocks if blocks else []
    
    async def run_stdio(self) -> None:
        """STDIO transport로 서버 실행"""
        if not self._initialized:
            raise RuntimeError("Server not initialized. Call initialize() first.")
        
        logger.info("Running MCP server with STDIO transport")
        await self.app.run()
    
    async def run_websocket(self, port: int = 3000) -> None:
        """WebSocket transport로 서버 실행 (향후 구현)"""
        if not self._initialized:
            raise RuntimeError("Server not initialized. Call initialize() first.")
        
        # WebSocket 구현은 향후 확장
        raise NotImplementedError("WebSocket transport not implemented yet")
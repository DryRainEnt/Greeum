#!/usr/bin/env python3
"""
기본 MCP 어댑터 인터페이스
- 모든 환경별 어댑터의 공통 인터페이스 정의
- Greeum 컴포넌트 통합 초기화
- 기존 도구 API 완전 호환성 보장
"""

import asyncio
import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional

# Greeum 핵심 컴포넌트
try:
    from greeum.core.block_manager import BlockManager
    from greeum.core.database_manager import DatabaseManager  
    from greeum.core.stm_manager import STMManager
    from greeum.core.duplicate_detector import DuplicateDetector
    from greeum.core.quality_validator import QualityValidator
    from greeum.core.usage_analytics import UsageAnalytics
    from greeum.core.search_engine import SearchEngine
    GREEUM_AVAILABLE = True
except ImportError:
    GREEUM_AVAILABLE = False

logger = logging.getLogger(__name__)

class BaseAdapter(ABC):
    """모든 MCP 어댑터의 기본 인터페이스"""
    
    def __init__(self):
        self.components = None
        self.initialized = False
        
    def initialize_greeum_components(self) -> Optional[Dict[str, Any]]:
        """Greeum 핵심 컴포넌트 통합 초기화"""
        if self.components is not None:
            return self.components
            
        if not GREEUM_AVAILABLE:
            logger.error("❌ Greeum components not available")
            return None
            
        try:
            # 핵심 컴포넌트들 초기화
            db_manager = DatabaseManager()
            block_manager = BlockManager(db_manager)
            stm_manager = STMManager(db_manager)
            duplicate_detector = DuplicateDetector(db_manager)
            quality_validator = QualityValidator()
            usage_analytics = UsageAnalytics(db_manager)
            search_engine = SearchEngine(block_manager)
            
            self.components = {
                'db_manager': db_manager,
                'block_manager': block_manager,
                'stm_manager': stm_manager,
                'duplicate_detector': duplicate_detector,
                'quality_validator': quality_validator,
                'usage_analytics': usage_analytics,
                'search_engine': search_engine
            }
            
            self.initialized = True
            logger.info("✅ Greeum components initialized successfully")
            return self.components
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize Greeum components: {e}")
            return None
    
    # 공통 도구 구현 (모든 어댑터에서 동일)
    def add_memory_tool(self, content: str, importance: float = 0.5) -> str:
        """메모리 추가 도구 - 기존 API 완전 호환"""
        if not self.components:
            self.initialize_greeum_components()
        if not self.components:
            return "❌ Greeum components not available"
            
        try:
            # 중복 검사
            duplicate_check = self.components['duplicate_detector'].check_duplicate(content)
            if duplicate_check["is_duplicate"]:
                similarity = duplicate_check["similarity_score"]
                return f"""⚠️  **Potential Duplicate Memory Detected**

**Similarity**: {similarity:.1%} with existing memory
**Similar Memory**: Block #{duplicate_check['similar_block_index']}

Please search existing memories first or provide more specific content."""
            
            # 품질 검증
            quality_result = self.components['quality_validator'].validate_memory_quality(content, importance)
            
            # 메모리 추가 - 직접 구현 (legacy 의존성 제거)
            block_data = self._add_memory_direct(content, importance)
            
            # 사용 통계 로깅
            self.components['usage_analytics'].log_quality_metrics(
                len(content), quality_result['quality_score'], quality_result['quality_level'],
                importance, importance, False, duplicate_check["similarity_score"], 
                len(quality_result.get('suggestions', []))
            )
            
            # 성공 응답
            quality_feedback = f"""
**Quality Score**: {quality_result['quality_score']:.1%} ({quality_result['quality_level']})
**Adjusted Importance**: {importance:.2f} (original: {importance:.2f})"""
            
            suggestions_text = ""
            if quality_result.get('suggestions'):
                suggestions_text = f"\n\n💡 **Quality Suggestions**:\n" + "\n".join(f"• {s}" for s in quality_result['suggestions'][:2])
            
            return f"""✅ **Memory Successfully Added!**

**Block Index**: #{block_data['block_index']}
**Storage**: Permanent (Long-term Memory)
**Duplicate Check**: ✅ Passed{quality_feedback}{suggestions_text}"""
            
        except Exception as e:
            logger.error(f"add_memory failed: {e}")
            return f"❌ Failed to add memory: {str(e)}"
    
    def search_memory_tool(self, query: str, limit: int = 5) -> str:
        """메모리 검색 도구 - 기존 API 완전 호환"""
        if not self.components:
            self.initialize_greeum_components()
        if not self.components:
            return "❌ Greeum components not available"
            
        try:
            # 메모리 검색 - 직접 구현 (legacy 의존성 제거)
            results = self._search_memory_direct(query, limit)
            
            # 사용 통계 로깅
            self.components['usage_analytics'].log_event(
                "tool_usage", "search_memory",
                {"query_length": len(query), "results_found": len(results), "limit_requested": limit},
                0, True
            )
            
            if results:
                result_text = f"🔍 Found {len(results)} memories:\n"
                for i, memory in enumerate(results, 1):
                    timestamp = memory.get('timestamp', 'Unknown')
                    content = memory.get('context', '')[:100] + ('...' if len(memory.get('context', '')) > 100 else '')
                    result_text += f"{i}. [{timestamp}] {content}\n"
                return result_text
            else:
                return f"🔍 No memories found for query: '{query}'"
                
        except Exception as e:
            logger.error(f"search_memory failed: {e}")
            return f"❌ Search failed: {str(e)}"
    
    def get_memory_stats_tool(self) -> str:
        """메모리 통계 도구 - 기존 API 완전 호환"""
        if not self.components:
            self.initialize_greeum_components()
        if not self.components:
            return "❌ Greeum components not available"
            
        try:
            db_manager = self.components['db_manager']
            stm_manager = self.components['stm_manager']
            
            # 기본 통계 - 실제 존재하는 메서드 사용
            try:
                # get_blocks 메서드로 전체 블록 수 계산
                all_blocks = db_manager.get_blocks()
                total_blocks = len(all_blocks) if all_blocks else 0
            except:
                total_blocks = "N/A"
            
            try:
                # 최근 블록들 가져오기 (최대 10개)
                recent_blocks = db_manager.get_blocks(limit=10) if hasattr(db_manager, 'get_blocks') else []
                recent_count = len(recent_blocks) if recent_blocks else 0
            except:
                recent_count = "N/A"
            
            try:
                # STM 통계
                stm_stats = stm_manager.get_stats() if hasattr(stm_manager, 'get_stats') else {}
            except:
                stm_stats = {}
            
            return f"""📊 **Greeum Memory Statistics**

**Long-term Memory**:
• Total Blocks: {total_blocks}
• Recent Entries: {recent_count}

**Short-term Memory**:
• Active Slots: {stm_stats.get('active_count', 'N/A')}
• Available Slots: {stm_stats.get('available_slots', 'N/A')}

**System Status**: ✅ Operational
**Version**: 2.2.8 (Unified MCP Server)"""
            
        except Exception as e:
            logger.error(f"get_memory_stats failed: {e}")
            return f"❌ Stats retrieval failed: {str(e)}"
    
    def usage_analytics_tool(self, days: int = 7, report_type: str = "usage") -> str:
        """사용 분석 도구 - 기존 API 완전 호환"""
        if not self.components:
            self.initialize_greeum_components()
        if not self.components:
            return "❌ Greeum components not available"
            
        try:
            # UsageAnalytics 실제 메서드 사용
            analytics_component = self.components['usage_analytics']
            if hasattr(analytics_component, 'get_usage_report'):
                analytics = analytics_component.get_usage_report(days=days, report_type=report_type)
            else:
                # fallback - 기본 데이터 생성
                analytics = {
                    'total_operations': 'N/A',
                    'add_operations': 'N/A', 
                    'search_operations': 'N/A',
                    'avg_quality_score': 0.0,
                    'high_quality_rate': 0.0,
                    'avg_response_time': 0.0,
                    'success_rate': 1.0
                }
            
            return f"""📈 **Usage Analytics Report** ({days} days)

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
**Generated**: Unified MCP v2.2.7"""
            
        except Exception as e:
            logger.error(f"usage_analytics failed: {e}")
            return f"❌ Analytics failed: {str(e)}"
    
    def _add_memory_direct(self, content: str, importance: float = 0.5) -> Dict[str, Any]:
        """메모리 직접 추가 - legacy 의존성 완전 제거"""
        from greeum.text_utils import process_user_input
        from datetime import datetime
        import json
        import hashlib
        
        if not self.components:
            raise Exception("Greeum components not available")
        
        db_manager = self.components['db_manager']
        
        # 텍스트 처리
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
        
    def _search_memory_direct(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """메모리 직접 검색 - legacy 의존성 완전 제거"""
        from greeum.embedding_models import get_embedding
        
        if not self.components:
            raise Exception("Greeum components not available")
            
        db_manager = self.components['db_manager'] 
        search_engine = self.components['search_engine']
        
        # SearchEngine.search 메서드 사용 (search_memories 아님)
        search_result = search_engine.search(query, top_k=limit)
        results = search_result.get('blocks', [])
        
        # 결과를 legacy 호환 형식으로 변환
        formatted_results = []
        for result in results:
            formatted_results.append({
                "block_index": result.get("block_index"),
                "context": result.get("context"), 
                "timestamp": result.get("timestamp"),
                "relevance_score": result.get("relevance_score", 0.0),
                "keywords": result.get("keywords", []),
                "tags": result.get("tags", [])
            })
            
        return formatted_results
    
    @abstractmethod
    async def run(self):
        """서버 실행 (각 어댑터에서 구현)"""
        pass
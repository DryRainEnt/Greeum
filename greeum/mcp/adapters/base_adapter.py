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
    from greeum.core import DatabaseManager  # Thread-safe factory pattern  
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
            logger.error("[ERROR] Greeum components not available")
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
            logger.error(f"[ERROR] Failed to initialize Greeum components: {e}")
            return None
    
    # 공통 도구 구현 (모든 어댑터에서 동일)
    def add_memory_tool(self, content: str, importance: float = 0.5) -> str:
        """메모리 추가 도구 - 기존 API 완전 호환"""
        if not self.components:
            self.initialize_greeum_components()
        if not self.components:
            return "[ERROR] Greeum components not available"
            
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
            return f"[ERROR] Failed to add memory: {str(e)}"
    
    def search_memory_tool(self, query: str, limit: int = 5, depth: int = 0, tolerance: float = 0.5) -> str:
        """메모리 검색 도구 - 연관관계 확장 탐색 기능 추가"""
        if not self.components:
            self.initialize_greeum_components()
        if not self.components:
            return "[ERROR] Greeum components not available"
            
        try:
            # 기본 메모리 검색
            results = self._search_memory_direct(query, limit)
            
            # 연관관계 확장 탐색 (depth > 0인 경우)
            if depth > 0 and results:
                results = self._expand_search_with_associations(results, depth, tolerance, limit)
            
            # 사용 통계 로깅 (확장된 파라미터 포함)
            self.components['usage_analytics'].log_event(
                "tool_usage", "search_memory",
                {
                    "query_length": len(query), 
                    "results_found": len(results), 
                    "limit_requested": limit,
                    "depth": depth,
                    "tolerance": tolerance
                },
                0, True
            )
            
            if results:
                result_text = f"🔍 Found {len(results)} memories"
                if depth > 0:
                    result_text += f" (depth {depth}, tolerance {tolerance:.1f})"
                result_text += ":\n"
                
                for i, memory in enumerate(results, 1):
                    timestamp = memory.get('timestamp', 'Unknown')
                    content = memory.get('context', '')[:100] + ('...' if len(memory.get('context', '')) > 100 else '')
                    
                    # 연관관계 표시 (있는 경우)
                    relation_info = ""
                    if memory.get('relation_type'):
                        if memory['relation_type'] == 'direct_match':
                            relation_info = " [🎯]"
                        elif 'depth_1' in memory['relation_type']:
                            relation_info = " [[LINK]]"
                        elif 'depth_2' in memory['relation_type']:
                            relation_info = " [[LINK][LINK]]"
                        elif 'depth_3' in memory['relation_type']:
                            relation_info = " [[LINK][LINK][LINK]]"
                    
                    result_text += f"{i}. [{timestamp}]{relation_info} {content}\n"
                return result_text
            else:
                return f"🔍 No memories found for query: '{query}'"
                
        except Exception as e:
            logger.error(f"search_memory failed: {e}")
            return f"[ERROR] Search failed: {str(e)}"
    
    def get_memory_stats_tool(self) -> str:
        """메모리 통계 도구 - 로컬 DB 기준으로 정확한 통계 제공"""
        if not self.components:
            self.initialize_greeum_components()
        if not self.components:
            return "[ERROR] Greeum components not available"
            
        try:
            db_manager = self.components['db_manager']
            stm_manager = self.components['stm_manager']
            
            # 직접 SQL을 사용한 정확한 통계 계산
            stats = self._get_detailed_memory_stats(db_manager)
            
            # STM 통계
            stm_stats = {}
            try:
                if hasattr(stm_manager, 'get_stats'):
                    stm_stats = stm_manager.get_stats()
                elif hasattr(stm_manager, 'cache'):
                    # STM 캐시 직접 확인
                    cache_data = stm_manager.cache
                    stm_stats = {
                        'active_count': len(cache_data) if isinstance(cache_data, dict) else 0,
                        'available_slots': max(0, 100 - len(cache_data)) if isinstance(cache_data, dict) else 100
                    }
            except:
                stm_stats = {'active_count': 0, 'available_slots': 100}
            
            return f"""📊 **Greeum Memory Statistics**

**Long-term Memory (Local DB)**:
• Total Blocks: {stats['total_blocks']}
• This Week: {stats['week_count']}
• This Month: {stats['month_count']}
• Average Importance: {stats['avg_importance']:.2f}

**Short-term Memory**:
• Active Slots: {stm_stats.get('active_count', 0)}
• Available Slots: {stm_stats.get('available_slots', 100)}

**Database Info**:
• Database Path: {stats['db_path']}
• Last Updated: {stats['last_updated']}

**System Status**: ✅ Operational
**Version**: 2.3.0 (Local DB Optimized)"""
            
        except Exception as e:
            logger.error(f"get_memory_stats failed: {e}")
            return f"[ERROR] Stats retrieval failed: {str(e)}"
    
    def usage_analytics_tool(self, days: int = 7, report_type: str = "usage") -> str:
        """사용 분석 도구 - 기존 API 완전 호환"""
        if not self.components:
            self.initialize_greeum_components()
        if not self.components:
            return "[ERROR] Greeum components not available"
            
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
            
            return f"""[IMPROVE] **Usage Analytics Report** ({days} days)

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
            return f"[ERROR] Analytics failed: {str(e)}"
    
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
    
    def _expand_search_with_associations(self, base_results: List[Dict], depth: int, tolerance: float, max_results: int) -> List[Dict]:
        """
        연관관계를 활용한 확장 검색
        
        Args:
            base_results: 기본 검색 결과
            depth: 탐색 깊이 (1-3)
            tolerance: 연관관계 허용 오차 (0.0-1.0)
            max_results: 최대 결과 수
            
        Returns:
            확장된 검색 결과 (연관관계 정보 포함)
        """
        try:
            if not base_results or depth == 0:
                return base_results
            
            # AssociationSystem 초기화
            from greeum.core.association_detector import AssociationSystem
            association_system = AssociationSystem()
            
            db_manager = self.components['db_manager']
            expanded_results = []
            processed_indices = set()
            
            # 기본 결과들을 먼저 추가 (원본 표시)
            for memory in base_results:
                memory['relation_type'] = 'direct_match'
                expanded_results.append(memory)
                processed_indices.add(memory.get('block_index'))
            
            current_level_memories = base_results.copy()
            
            # 각 depth 단계별로 연관 메모리 탐색
            for current_depth in range(1, depth + 1):
                if len(expanded_results) >= max_results:
                    break
                    
                next_level_memories = []
                
                for memory in current_level_memories:
                    if len(expanded_results) >= max_results:
                        break
                    
                    # 현재 메모리와 연관된 메모리들 찾기
                    associated_memories = self._find_associated_memories(
                        memory, association_system, tolerance, current_depth
                    )
                    
                    for assoc_memory in associated_memories:
                        if len(expanded_results) >= max_results:
                            break
                            
                        assoc_index = assoc_memory.get('block_index')
                        if assoc_index not in processed_indices:
                            assoc_memory['relation_type'] = f'depth_{current_depth}_association'
                            expanded_results.append(assoc_memory)
                            processed_indices.add(assoc_index)
                            next_level_memories.append(assoc_memory)
                
                current_level_memories = next_level_memories
                
                # 더 이상 새로운 연관 메모리가 없으면 중단
                if not next_level_memories:
                    break
            
            return expanded_results[:max_results]
            
        except Exception as e:
            logger.error(f"Association expansion failed: {e}")
            # 실패 시 기본 결과 반환
            return base_results
    
    def _find_associated_memories(self, memory: Dict, association_system, tolerance: float, depth: int) -> List[Dict]:
        """
        특정 메모리와 연관된 메모리들 찾기
        
        Args:
            memory: 기준 메모리
            association_system: 연관관계 시스템
            tolerance: 허용 오차
            depth: 현재 탐색 깊이
            
        Returns:
            연관된 메모리 리스트
        """
        try:
            db_manager = self.components['db_manager']
            
            # 연관도 임계값 계산 (tolerance 기반)
            base_threshold = 0.1  # 기본 임계값
            adjusted_threshold = base_threshold * (1.0 - tolerance)  # tolerance 높을수록 낮은 임계값
            
            # 유사도 기반 연관 메모리 검색
            if memory.get('embedding'):
                similar_memories = db_manager.search_blocks_by_embedding(
                    memory['embedding'], 
                    top_k=20,  # 후보군을 넉넉히
                    threshold=adjusted_threshold
                )
                
                # 현재 메모리 제외
                current_index = memory.get('block_index')
                filtered_memories = [m for m in similar_memories if m.get('block_index') != current_index]
                
                # tolerance 기반으로 추가 필터링
                final_memories = []
                for candidate in filtered_memories[:10]:  # 상위 10개만 고려
                    # tolerance가 높을수록 더 많은 메모리 포함
                    similarity_score = self._calculate_similarity(memory, candidate)
                    if similarity_score >= adjusted_threshold:
                        final_memories.append(candidate)
                
                return final_memories
            
            return []
            
        except Exception as e:
            logger.error(f"Finding associated memories failed: {e}")
            return []
    
    def _calculate_similarity(self, memory1: Dict, memory2: Dict) -> float:
        """
        두 메모리 간 유사도 계산 (간단한 구현)
        
        실제로는 임베딩 코사인 유사도, 키워드 겹침 등을 종합
        """
        try:
            import numpy as np
            
            # 임베딩 유사도 계산
            emb1 = memory1.get('embedding', [])
            emb2 = memory2.get('embedding', [])
            
            if emb1 and emb2 and len(emb1) == len(emb2):
                emb1_np = np.array(emb1)
                emb2_np = np.array(emb2)
                
                # 코사인 유사도
                dot_product = np.dot(emb1_np, emb2_np)
                norm1 = np.linalg.norm(emb1_np)
                norm2 = np.linalg.norm(emb2_np)
                
                if norm1 > 0 and norm2 > 0:
                    return dot_product / (norm1 * norm2)
            
            # 폴백: 키워드 기반 유사도
            keywords1 = set(memory1.get('keywords', []))
            keywords2 = set(memory2.get('keywords', []))
            
            if keywords1 and keywords2:
                intersection = keywords1.intersection(keywords2)
                union = keywords1.union(keywords2)
                return len(intersection) / len(union) if union else 0.0
            
            return 0.0
            
        except Exception as e:
            logger.error(f"Similarity calculation failed: {e}")
            return 0.0
    
    def _get_detailed_memory_stats(self, db_manager) -> Dict[str, Any]:
        """로컬 DB에서 상세한 메모리 통계 직접 계산"""
        try:
            from datetime import datetime, timedelta
            import sqlite3
            
            # DB 연결 정보 가져오기
            db_path = getattr(db_manager, 'db_path', 'Unknown')
            
            # 직접 SQL 쿼리 실행 - 로컬 DB 우선
            if hasattr(db_manager, 'conn') and db_manager.conn:
                conn = db_manager.conn
            elif hasattr(db_manager, 'db_path'):
                conn = sqlite3.connect(db_manager.db_path)
            else:
                # 로컬 디렉토리 데이터베이스 경로 확인
                import os
                local_db_path = './data/memory.db'
                if os.path.exists(local_db_path):
                    conn = sqlite3.connect(local_db_path)
                else:
                    # 대체 로컬 경로들 시도
                    alternative_paths = [
                        './memory.db',
                        './greeum_memory.db',
                        os.path.expanduser('~/greeum_local/memory.db')
                    ]
                    conn = None
                    for path in alternative_paths:
                        if os.path.exists(path):
                            conn = sqlite3.connect(path)
                            break
                    
                    if not conn:
                        raise FileNotFoundError("No local memory database found. Please ensure memory.db exists in current directory.")
            
            cursor = conn.cursor()
            
            # 전체 블록 수
            cursor.execute("SELECT COUNT(*) FROM blocks")
            total_blocks = cursor.fetchone()[0]
            
            # 이번 주 블록 수
            week_ago = (datetime.now() - timedelta(days=7)).isoformat()
            cursor.execute("SELECT COUNT(*) FROM blocks WHERE timestamp > ?", (week_ago,))
            week_count = cursor.fetchone()[0]
            
            # 이번 달 블록 수  
            month_ago = (datetime.now() - timedelta(days=30)).isoformat()
            cursor.execute("SELECT COUNT(*) FROM blocks WHERE timestamp > ?", (month_ago,))
            month_count = cursor.fetchone()[0]
            
            # 평균 중요도
            cursor.execute("SELECT AVG(importance) FROM blocks WHERE importance IS NOT NULL")
            avg_importance_result = cursor.fetchone()[0]
            avg_importance = avg_importance_result if avg_importance_result else 0.5
            
            # 마지막 업데이트
            cursor.execute("SELECT timestamp FROM blocks ORDER BY block_index DESC LIMIT 1")
            last_entry = cursor.fetchone()
            last_updated = last_entry[0] if last_entry else "Never"
            
            # 연결이 임시로 생성된 경우 닫기
            if not (hasattr(db_manager, 'conn') and db_manager.conn):
                conn.close()
            
            return {
                'total_blocks': total_blocks,
                'week_count': week_count,
                'month_count': month_count,
                'avg_importance': avg_importance,
                'db_path': db_path,
                'last_updated': last_updated
            }
            
        except Exception as e:
            logger.error(f"Failed to get detailed stats: {e}")
            return {
                'total_blocks': 0,
                'week_count': 0,
                'month_count': 0,
                'avg_importance': 0.5,
                'db_path': 'Unknown',
                'last_updated': 'Error'
            }
    
    @abstractmethod
    async def run(self):
        """서버 실행 (각 어댑터에서 구현)"""
        pass
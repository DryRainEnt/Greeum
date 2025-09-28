#!/usr/bin/env python3
"""
Smart Duplicate Detection for Greeum v2.0.5
- Prevents redundant memory storage
- Uses both semantic similarity and text matching
- Provides intelligent recommendations
"""

import difflib
import hashlib
import logging
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class DuplicateDetector:
    """지능적 중복 검사 엔진"""
    
    def __init__(self, db_manager, similarity_threshold: float = 0.85):
        """
        중복 검사기 초기화
        
        Args:
            db_manager: DatabaseManager 인스턴스
            similarity_threshold: 중복 판정 임계값 (0.0-1.0)
        """
        self.db_manager = db_manager
        self.similarity_threshold = similarity_threshold
        self.exact_match_threshold = 0.95  # 거의 동일한 내용
        self.partial_match_threshold = 0.7  # 유사한 내용
        
    def check_duplicate(self, content: str, importance: float = 0.5, 
                       context_window_hours: int = 24) -> Dict[str, Any]:
        """
        중복 검사 수행
        
        Args:
            content: 검사할 내용
            importance: 중요도 점수
            context_window_hours: 최근 N시간 내 중복 검사 (성능 최적화)
            
        Returns:
            {
                "is_duplicate": bool,
                "duplicate_type": str,  # "exact", "similar", "none"
                "similar_memories": List[Dict],
                "similarity_score": float,
                "recommendation": str,
                "suggested_action": str  # "skip", "merge", "store_anyway"
            }
        """
        try:
            # 1. 빈 내용 체크
            if not content or len(content.strip()) < 3:
                return self._create_result(False, "none", [], 0.0, 
                                         "Content too short for meaningful duplicate check",
                                         "skip")
            
            # 2. 최근 메모리에서 유사한 내용 검색
            similar_memories = self._find_similar_memories(content, context_window_hours)
            
            if not similar_memories:
                return self._create_result(False, "none", [], 0.0,
                                         "✅ No similar memories found - safe to store",
                                         "store_anyway")
            
            # 3. 유사도 분석
            best_match = self._analyze_similarity(content, similar_memories)
            
            # 4. 중복 타입 결정
            duplicate_type, is_duplicate = self._classify_duplicate(best_match["similarity"])
            
            # 5. 권장사항 생성
            recommendation, suggested_action = self._generate_recommendation(
                duplicate_type, best_match, importance
            )
            
            return self._create_result(
                is_duplicate, duplicate_type, similar_memories[:3],
                best_match["similarity"], recommendation, suggested_action
            )
            
        except Exception as e:
            logger.error(f"Duplicate detection failed: {e}")
            return self._create_result(False, "error", [], 0.0,
                                     f"⚠️ Duplicate check failed: {str(e)}",
                                     "store_anyway")
    
    def _find_similar_memories(self, content: str, context_window_hours: int) -> List[Dict[str, Any]]:
        """최근 메모리에서 유사한 내용 검색"""
        try:
            # 1. 임베딩 기반 검색 시도
            from greeum.embedding_models import get_embedding
            
            embedding = get_embedding(content)
            search_fn = getattr(self.db_manager, "search_blocks_by_embedding", None)
            if callable(search_fn):
                try:
                    similar_blocks = search_fn(
                        embedding, top_k=10, min_similarity=0.6
                    )
                except TypeError:
                    similar_blocks = search_fn(embedding, top_k=10)
                if similar_blocks:
                    return similar_blocks
                
        except Exception as e:
            logger.debug(f"Embedding search failed, falling back to keyword search: {e}")
        
        # 2. 키워드 기반 검색 (fallback)
        keywords = self._extract_keywords(content)
        if keywords:
            keyword_fn = getattr(self.db_manager, "search_blocks_by_keyword", None)
            if callable(keyword_fn):
                try:
                    results = keyword_fn(keywords, limit=10)
                    if results:
                        return results
                except Exception as keyword_error:
                    logger.debug("Keyword fallback failed: %s", keyword_error)
        
        # 3. 최근 메모리 기반 검색 (최후 수단)
        history_fn = getattr(self.db_manager, "get_blocks_since_time", None)
        if callable(history_fn):
            cutoff_time = datetime.now() - timedelta(hours=context_window_hours)
            try:
                return history_fn(cutoff_time.isoformat(), limit=20)
            except Exception as history_error:
                logger.debug("Recent-block fallback failed: %s", history_error)

        return []
    
    def _extract_keywords(self, content: str) -> List[str]:
        """간단한 키워드 추출"""
        # 기본적인 키워드 추출 (향후 더 정교한 방식으로 개선 가능)
        words = content.lower().split()
        # 불용어 제거 및 길이 필터링
        stop_words = {"the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for", "of", "with", "by"}
        keywords = [word.strip(".,!?;:") for word in words 
                   if len(word) > 3 and word not in stop_words]
        return keywords[:5]  # 상위 5개 키워드만
    
    def _analyze_similarity(self, content: str, similar_memories: List[Dict[str, Any]]) -> Dict[str, Any]:
        """유사도 분석 및 최고 매치 찾기"""
        best_match = {"memory": None, "similarity": 0.0, "match_type": "none"}
        
        content_lower = content.lower().strip()
        content_hash = hashlib.md5(content_lower.encode()).hexdigest()
        
        for memory in similar_memories:
            memory_content = memory.get("context", "").lower().strip()
            
            # 1. 정확한 해시 매치 (exact duplicate)
            memory_hash = hashlib.md5(memory_content.encode()).hexdigest()
            if content_hash == memory_hash:
                return {"memory": memory, "similarity": 1.0, "match_type": "exact_hash"}
            
            # 2. 텍스트 유사도 계산
            similarity = difflib.SequenceMatcher(None, content_lower, memory_content).ratio()
            
            # 3. 더 나은 매치 발견시 업데이트
            if similarity > best_match["similarity"]:
                best_match = {
                    "memory": memory,
                    "similarity": similarity,
                    "match_type": "text_similarity"
                }
        
        return best_match
    
    def _classify_duplicate(self, similarity_score: float) -> Tuple[str, bool]:
        """유사도 점수를 기반으로 중복 타입 분류"""
        if similarity_score >= self.exact_match_threshold:
            return "exact", True
        elif similarity_score >= self.similarity_threshold:
            return "similar", True
        elif similarity_score >= self.partial_match_threshold:
            return "partial", False
        else:
            return "none", False
    
    def _generate_recommendation(self, duplicate_type: str, best_match: Dict[str, Any], 
                               importance: float) -> Tuple[str, str]:
        """권장사항 및 제안 액션 생성"""
        if duplicate_type == "exact":
            memory = best_match["memory"]
            block_index = memory.get("block_index", "unknown")
            return (
                f"🚫 Exact duplicate detected! Very similar content already exists in Block #{block_index}. "
                f"Consider updating existing memory instead of creating new one.",
                "skip"
            )
        
        elif duplicate_type == "similar":
            memory = best_match["memory"]
            block_index = memory.get("block_index", "unknown")
            similarity = best_match["similarity"]
            return (
                f"⚠️ Similar content found (Block #{block_index}, {similarity:.1%} similar). "
                f"Review existing memory and add only truly new information.",
                "merge" if importance > 0.6 else "skip"
            )
        
        elif duplicate_type == "partial":
            similarity = best_match["similarity"]
            return (
                f"[NOTE] Partially similar content found ({similarity:.1%} match). "
                f"Content is different enough to store separately.",
                "store_anyway"
            )
        
        else:
            return (
                "✅ Unique content - safe to store without concerns.",
                "store_anyway"
            )
    
    def _create_result(self, is_duplicate: bool, duplicate_type: str, 
                      similar_memories: List[Dict[str, Any]], similarity_score: float,
                      recommendation: str, suggested_action: str) -> Dict[str, Any]:
        """결과 딕셔너리 생성"""
        return {
            "is_duplicate": is_duplicate,
            "duplicate_type": duplicate_type,
            "similar_memories": similar_memories,
            "similarity_score": similarity_score,
            "recommendation": recommendation,
            "suggested_action": suggested_action,
            "timestamp": datetime.now().isoformat()
        }
    
    def check_batch_duplicates(self, contents: List[str]) -> List[Dict[str, Any]]:
        """배치 중복 검사 (성능 최적화)"""
        results = []
        processed_hashes = set()
        
        for content in contents:
            # 배치 내 중복 체크
            content_hash = hashlib.md5(content.lower().strip().encode()).hexdigest()
            if content_hash in processed_hashes:
                results.append(self._create_result(
                    True, "batch_duplicate", [], 1.0,
                    "[PROCESS] Duplicate within current batch", "skip"
                ))
                continue
            
            processed_hashes.add(content_hash)
            results.append(self.check_duplicate(content))
        
        return results
    
    def get_duplicate_statistics(self, days: int = 7) -> Dict[str, Any]:
        """중복 검사 통계 생성"""
        try:
            cutoff_time = datetime.now() - timedelta(days=days)
            recent_memories = self.db_manager.get_blocks_since_time(
                cutoff_time.isoformat(), limit=1000
            )
            
            total_memories = len(recent_memories)
            if total_memories < 2:
                return {"period_days": days, "total_memories": total_memories, 
                       "estimated_duplicates": 0, "duplicate_rate": 0.0}
            
            # 간단한 중복률 추정
            duplicate_count = 0
            checked_hashes = set()
            
            for memory in recent_memories:
                content = memory.get("context", "").lower().strip()
                content_hash = hashlib.md5(content.encode()).hexdigest()
                
                if content_hash in checked_hashes:
                    duplicate_count += 1
                else:
                    checked_hashes.add(content_hash)
            
            duplicate_rate = duplicate_count / total_memories if total_memories > 0 else 0.0
            
            return {
                "period_days": days,
                "total_memories": total_memories,
                "unique_memories": len(checked_hashes),
                "estimated_duplicates": duplicate_count,
                "duplicate_rate": duplicate_rate,
                "recommendations": self._generate_statistics_recommendations(duplicate_rate)
            }
            
        except Exception as e:
            logger.error(f"Failed to generate duplicate statistics: {e}")
            return {"error": str(e)}
    
    def _generate_statistics_recommendations(self, duplicate_rate: float) -> List[str]:
        """통계 기반 권장사항 생성"""
        recommendations = []
        
        if duplicate_rate > 0.2:  # 20% 이상
            recommendations.append("[ALERT] High duplicate rate detected! Always search before storing new memories.")
        elif duplicate_rate > 0.1:  # 10% 이상
            recommendations.append("⚠️ Moderate duplicate rate. Consider using search_memory before add_memory.")
        else:
            recommendations.append("✅ Low duplicate rate - memory usage looks healthy!")
        
        if duplicate_rate > 0.05:  # 5% 이상
            recommendations.append("💡 Enable duplicate detection in your memory workflow.")
        
        return recommendations

if __name__ == "__main__":
    # 테스트 코드
    print("✅ DuplicateDetector module loaded successfully")
    print("📊 Key features:")
    print("  - Semantic similarity detection")
    print("  - Text-based duplicate matching")
    print("  - Intelligent recommendations")
    print("  - Batch processing support")
    print("  - Statistical analysis")

"""
Phase 3: LocalizedSearchEngine - 체크포인트 기반 지역 검색

이 모듈은 CheckpointManager가 생성한 체크포인트를 활용하여
전체 LTM 대신 관련성 높은 지역만 검색하는 지능적 검색 엔진입니다.
"""

import time
import numpy as np
from typing import Dict, List, Any, Optional, Tuple


class LocalizedSearchEngine:
    """체크포인트 기반 지역 검색"""
    
    def __init__(self, checkpoint_manager, block_manager):
        self.checkpoint_manager = checkpoint_manager
        self.block_manager = block_manager
        
        # 검색 설정
        self.min_slot_relevance = 0.3  # 슬롯 관련성 최소 임계값
        self.min_block_relevance = 0.2  # 블록 관련성 최소 임계값
        self.default_radius = 15  # 기본 검색 반경
        self.max_localized_blocks = 100  # 지역 검색 최대 블록 수
        self.max_fallback_retries = 3  # fallback 최대 재시도 횟수 (무한 재귀 방지)
        self.block_access_timeout = 5.0  # 블록 접근 타임아웃 (초)
        
        # 성능 모니터링
        self.stats = {
            "localized_searches": 0,
            "fallback_searches": 0,
            "total_blocks_searched": 0,
            "avg_search_time_ms": 0.0,
            "checkpoint_hit_rate": 0.0
        }
        
    def search_with_checkpoints(self, query_embedding: List[float], 
                              working_memory, top_k: int = 5) -> List[Dict[str, Any]]:
        """체크포인트 기반 지역 검색"""
        search_start = time.perf_counter()
        
        try:
            # 1. Working Memory의 활성 슬롯들에서 체크포인트 수집
            active_slots = working_memory.get_active_slots()
            
            if not active_slots:
                return self._fallback_search(query_embedding, top_k, "no_active_slots", 0)
            
            localized_results = []
            used_checkpoints = 0
            
            for slot in active_slots:
                # 슬롯과 쿼리의 관련성 계산
                slot_relevance = self._calculate_slot_relevance(
                    slot.embedding, 
                    query_embedding
                )
                
                print(f"    📍 슬롯 {slot.slot_id}: 관련성 {slot_relevance:.3f}")
                
                # 관련성이 높은 슬롯만 사용
                if slot_relevance > self.min_slot_relevance:
                    checkpoint_indices = self.checkpoint_manager.get_checkpoint_radius(
                        slot.slot_id, 
                        radius=self._calculate_dynamic_radius(slot_relevance)
                    )
                    
                    if checkpoint_indices:
                        # 체크포인트 접근 기록
                        self.checkpoint_manager.update_checkpoint_access(slot.slot_id)
                        used_checkpoints += 1
                        
                        # 체크포인트 주변 블록들만 검색
                        local_results = self._search_localized_blocks(
                            checkpoint_indices, 
                            query_embedding, 
                            top_k * 2  # 여유분 확보
                        )
                        
                        # 슬롯 관련성으로 가중치 적용
                        for result in local_results:
                            result["checkpoint_relevance"] = slot_relevance
                            result["source_slot"] = slot.slot_id
                            result["search_method"] = "checkpoint_localized"
                        
                        localized_results.extend(local_results)
                        
                        print(f"      ✅ 체크포인트 {len(checkpoint_indices)}개 블록 → {len(local_results)}개 결과")
                    else:
                        print(f"      ⚠️ 체크포인트 없음")
                else:
                    print(f"      [ERROR] 관련성 부족 (< {self.min_slot_relevance})")
            
            # 2. 체크포인트 결과 처리
            if localized_results and used_checkpoints > 0:
                final_results = self._process_localized_results(localized_results, top_k)
                search_time = (time.perf_counter() - search_start) * 1000
                
                # 통계 업데이트
                self._update_stats("localized", len(localized_results), search_time)
                
                print(f"    🎯 체크포인트 검색 성공: {len(final_results)}개 결과, {search_time:.2f}ms")
                return final_results
            else:
                return self._fallback_search(query_embedding, top_k, "no_checkpoint_results", 0)
                
        except Exception as e:
            print(f"    [ERROR] 체크포인트 검색 실패: {str(e)}")
            return self._fallback_search(query_embedding, top_k, "error", 0)
    
    def _search_localized_blocks(self, block_indices: List[int], 
                               query_embedding: List[float], limit: int) -> List[Dict[str, Any]]:
        """지정된 블록 인덱스들만 검색"""
        results = []
        searched_count = 0
        
        # 검색 범위 제한
        indices_to_search = block_indices[:min(limit, self.max_localized_blocks)]
        
        for block_index in indices_to_search:
            try:
                # 타임아웃을 고려한 블록 접근
                start_time = time.perf_counter()
                block = self.block_manager.get_block_by_index(block_index)
                access_time = time.perf_counter() - start_time
                
                # 타임아웃 체크
                if access_time > self.block_access_timeout:
                    print(f"      ⚠️ 블록 {block_index} 접근 타임아웃 ({access_time:.2f}s)")
                    continue
                
                searched_count += 1
                
                if block and "embedding" in block and block["embedding"]:
                    similarity = self._calculate_cosine_similarity(
                        query_embedding, 
                        block["embedding"]
                    )
                    
                    # 최소 관련성 임계값 확인
                    if similarity > self.min_block_relevance:
                        results.append({
                            "block_index": block_index,
                            "similarity_score": similarity,
                            "content": block.get("context", ""),
                            "keywords": block.get("keywords", []),
                            "timestamp": block.get("timestamp", ""),
                            "importance": block.get("importance", 0.5)
                        })
                        
            except Exception as e:
                # 개별 블록 접근 실패는 조용히 넘어감
                continue
        
        # 유사도 순으로 정렬
        results.sort(key=lambda x: x["similarity_score"], reverse=True)
        
        return results
    
    def _process_localized_results(self, localized_results: List[Dict[str, Any]], 
                                 top_k: int) -> List[Dict[str, Any]]:
        """지역 검색 결과 처리 및 통합"""
        
        # 중복 제거 (같은 블록 인덱스)
        unique_results = self._deduplicate_by_block_index(localized_results)
        
        # 종합 점수 계산 (원래 점수 + 체크포인트 관련성)
        for result in unique_results:
            original_score = result.get("similarity_score", 0.5)
            checkpoint_relevance = result.get("checkpoint_relevance", 0.3)
            importance = result.get("importance", 0.5)
            
            # 가중 평균으로 최종 점수 계산
            result["final_score"] = (
                original_score * 0.6 +           # 유사도 60%
                checkpoint_relevance * 0.3 +     # 체크포인트 관련성 30%
                importance * 0.1                 # 중요도 10%
            )
        
        # 최종 점수로 재정렬
        unique_results.sort(key=lambda x: x["final_score"], reverse=True)
        
        # 상위 결과만 반환
        return unique_results[:top_k]
    
    def _fallback_search(self, query_embedding: List[float], top_k: int, 
                        reason: str, _retry_count: int = 0) -> List[Dict[str, Any]]:
        """체크포인트 검색 실패 시 전체 LTM 검색 (재귀 제한 포함)"""
        # 무한 재귀 방지
        if _retry_count >= self.max_fallback_retries:
            print(f"    [ERROR] Fallback 최대 재시도 횟수 초과 ({_retry_count}/{self.max_fallback_retries})")
            return []
        fallback_start = time.perf_counter()
        
        try:
            print(f"    [PROCESS] Fallback 검색 시작 (이유: {reason})")
            
            # 전체 LTM 검색
            fallback_results = self.block_manager.search_by_embedding(
                query_embedding, top_k=top_k
            )
            
            # 검색 방법 표시
            for result in fallback_results:
                result["search_method"] = "ltm_fallback"
                result["fallback_reason"] = reason
            
            fallback_time = (time.perf_counter() - fallback_start) * 1000
            
            # 통계 업데이트
            self._update_stats("fallback", len(fallback_results), fallback_time)
            
            print(f"    ✅ Fallback 완료: {len(fallback_results)}개 결과, {fallback_time:.2f}ms")
            
            return fallback_results
            
        except Exception as e:
            print(f"    [ERROR] Fallback 검색 실패 (재시도 {_retry_count + 1}/{self.max_fallback_retries}): {str(e)}")
            
            # 재시도 가능한 경우 다시 시도
            if _retry_count < self.max_fallback_retries - 1:
                time.sleep(0.1)  # 짧은 대기 후 재시도
                return self._fallback_search(query_embedding, top_k, f"{reason}_retry", _retry_count + 1)
            else:
                print(f"    [ERROR] Fallback 최종 실패: 빈 결과 반환")
                return []
    
    def _calculate_slot_relevance(self, slot_embedding: List[float], 
                                query_embedding: List[float]) -> float:
        """슬롯과 쿼리 간의 관련성 계산"""
        try:
            return self._calculate_cosine_similarity(slot_embedding, query_embedding)
        except Exception:
            return 0.0
    
    def _calculate_dynamic_radius(self, slot_relevance: float) -> int:
        """슬롯 관련성에 따른 동적 검색 반경 계산"""
        # 관련성이 높을수록 더 넓은 반경으로 검색
        if slot_relevance > 0.8:
            return 20  # 매우 관련성 높음
        elif slot_relevance > 0.6:
            return 15  # 관련성 높음
        elif slot_relevance > 0.4:
            return 10  # 보통 관련성
        else:
            return 5   # 낮은 관련성
    
    def _calculate_cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """코사인 유사도 계산"""
        try:
            if not vec1 or not vec2:
                return 0.0
                
            # numpy 배열로 변환
            a = np.array(vec1)
            b = np.array(vec2)
            
            # 벡터 크기가 다르면 0 반환
            if len(a) != len(b):
                return 0.0
            
            # 코사인 유사도 계산
            dot_product = np.dot(a, b)
            norm_a = np.linalg.norm(a)
            norm_b = np.linalg.norm(b)
            
            if norm_a == 0 or norm_b == 0:
                return 0.0
            
            similarity = dot_product / (norm_a * norm_b)
            
            # -1 ~ 1 범위를 0 ~ 1 범위로 변환
            return max(0.0, min(1.0, (similarity + 1) / 2))
            
        except Exception as e:
            print(f"    ⚠️ 코사인 유사도 계산 실패: {str(e)}")
            return 0.0
    
    def _deduplicate_by_block_index(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """블록 인덱스 기준으로 중복 제거 (높은 점수 우선)"""
        seen_indices = set()
        unique_results = []
        
        # 점수 순으로 정렬 (높은 점수 우선)
        sorted_results = sorted(
            results, 
            key=lambda x: x.get("similarity_score", 0), 
            reverse=True
        )
        
        for result in sorted_results:
            block_index = result.get("block_index")
            if block_index is not None and block_index not in seen_indices:
                seen_indices.add(block_index)
                unique_results.append(result)
        
        return unique_results
    
    def _update_stats(self, search_type: str, result_count: int, search_time_ms: float):
        """검색 통계 업데이트"""
        if search_type == "localized":
            self.stats["localized_searches"] += 1
        elif search_type == "fallback":
            self.stats["fallback_searches"] += 1
        
        self.stats["total_blocks_searched"] += result_count
        
        # 평균 검색 시간 업데이트
        total_searches = self.stats["localized_searches"] + self.stats["fallback_searches"]
        if total_searches > 0:
            current_avg = self.stats["avg_search_time_ms"]
            self.stats["avg_search_time_ms"] = (
                (current_avg * (total_searches - 1) + search_time_ms) / total_searches
            )
            
            # 체크포인트 적중률 계산
            self.stats["checkpoint_hit_rate"] = (
                self.stats["localized_searches"] / total_searches
            )
    
    def get_stats(self) -> Dict[str, Any]:
        """지역 검색 엔진 통계 반환"""
        return {
            "localized_searches": self.stats["localized_searches"],
            "fallback_searches": self.stats["fallback_searches"],
            "total_searches": self.stats["localized_searches"] + self.stats["fallback_searches"],
            "checkpoint_hit_rate": round(self.stats["checkpoint_hit_rate"], 3),
            "avg_search_time_ms": round(self.stats["avg_search_time_ms"], 3),
            "total_blocks_searched": self.stats["total_blocks_searched"]
        }
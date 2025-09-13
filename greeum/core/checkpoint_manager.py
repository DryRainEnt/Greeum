"""
Phase 3: CheckpointManager - Working Memory와 LTM 간 체크포인트 관리

이 모듈은 Working Memory 슬롯과 LTM 블록 간의 지능적 체크포인트 연결을 관리합니다.
체크포인트를 통해 전체 LTM 검색 대신 관련성 높은 지역만 검색하여 성능을 향상시킵니다.
"""

import time
import hashlib
import json
import threading
from datetime import datetime
from typing import Dict, List, Any, Optional
import numpy as np


class CheckpointManager:
    """Working Memory와 LTM 간의 체크포인트 관리"""
    
    def __init__(self, db_manager, block_manager):
        self.db_manager = db_manager
        self.block_manager = block_manager
        self.checkpoint_cache = {}  # 메모리 내 캐시
        self._cache_lock = threading.RLock()  # 동시성 안전성을 위한 재귀 락
        self.max_checkpoints_per_slot = 10  # 슬롯당 최대 체크포인트 (8개 블록 처리 보장)
        self.max_cache_size = 1000  # 캐시 크기 제한 (메모리 사용량 제어)
        self.min_relevance_threshold = 0.3  # 최소 관련성 임계값
        
        # 성능 모니터링
        self.stats = {
            "checkpoints_created": 0,
            "checkpoints_accessed": 0,
            "cache_hits": 0,
            "cache_misses": 0
        }
        
    def create_checkpoint(self, working_memory_slot, related_blocks: List[Dict]) -> Dict[str, Any]:
        """Working Memory 슬롯에 LTM 체크포인트 생성"""
        start_time = time.perf_counter()
        
        try:
            # 컨텍스트 해시 계산
            context_hash = self._compute_context_hash(working_memory_slot.context)
            
            # 체크포인트 데이터 구성
            checkpoint_data = {
                "slot_id": working_memory_slot.slot_id,
                "context_hash": context_hash,
                "context_preview": working_memory_slot.context[:100],  # 디버깅용
                "ltm_blocks": [],
                "created_at": datetime.now().isoformat(),
                "last_accessed": datetime.now().isoformat(),
                "access_count": 0,
                "relevance_scores": []
            }
            
            # 관련 블록들 처리
            for i, block in enumerate(related_blocks[:self.max_checkpoints_per_slot]):
                if not isinstance(block, dict) or "block_index" not in block:
                    continue
                    
                # 의미적 거리 계산
                distance = self._calculate_semantic_distance(
                    working_memory_slot.embedding, 
                    block.get("embedding", [])
                )
                
                relevance_score = block.get("similarity_score", 0.5)
                
                block_data = {
                    "block_index": block["block_index"],
                    "relevance_score": relevance_score,
                    "semantic_distance": distance,
                    "keywords": block.get("keywords", []),
                    "content_preview": block.get("context", "")[:50],
                    "created_at": datetime.now().isoformat()
                }
                
                checkpoint_data["ltm_blocks"].append(block_data)
                checkpoint_data["relevance_scores"].append(relevance_score)
            
            # 평균 관련성 계산
            if checkpoint_data["relevance_scores"]:
                checkpoint_data["avg_relevance"] = np.mean(checkpoint_data["relevance_scores"])
            else:
                checkpoint_data["avg_relevance"] = 0.0
            
            # 메모리 내 캐시에 저장 (스레드 안전)
            with self._cache_lock:
                # 캐시 크기 제한 확인
                if len(self.checkpoint_cache) >= self.max_cache_size:
                    self._cleanup_cache_by_size()
                
                self.checkpoint_cache[working_memory_slot.slot_id] = checkpoint_data
            
            # 통계 업데이트
            self.stats["checkpoints_created"] += 1
            
            # 성능 로깅
            creation_time = (time.perf_counter() - start_time) * 1000
            print(f"    ✅ 체크포인트 생성: 슬롯 {working_memory_slot.slot_id}, "
                  f"{len(checkpoint_data['ltm_blocks'])}개 블록, "
                  f"평균 관련성: {checkpoint_data['avg_relevance']:.3f}, "
                  f"시간: {creation_time:.2f}ms")
            
            return checkpoint_data
            
        except Exception as e:
            print(f"    [ERROR] 체크포인트 생성 실패: {str(e)}")
            return {}
    
    def update_checkpoint_access(self, slot_id: str) -> bool:
        """체크포인트 접근 시간 업데이트 (스레드 안전)"""
        with self._cache_lock:
            if slot_id in self.checkpoint_cache:
                self.checkpoint_cache[slot_id]["last_accessed"] = datetime.now().isoformat()
                self.checkpoint_cache[slot_id]["access_count"] += 1
                self.stats["checkpoints_accessed"] += 1
                self.stats["cache_hits"] += 1
                return True
            else:
                self.stats["cache_misses"] += 1
                return False
    
    def get_checkpoint_radius(self, slot_id: str, radius: int = 15) -> List[int]:
        """체크포인트 주변 블록 인덱스 반환 (스레드 안전)"""
        with self._cache_lock:
            if slot_id not in self.checkpoint_cache:
                return []
        
            checkpoint = self.checkpoint_cache[slot_id]
        all_indices = []
        
        try:
            for block_data in checkpoint["ltm_blocks"]:
                center_index = block_data["block_index"]
                
                # block_index를 정수로 변환 (문자열일 수 있음)
                try:
                    center_index = int(center_index)
                except (ValueError, TypeError):
                    print(f"    ⚠️ 잘못된 block_index 형식: {center_index}")
                    continue
                
                # 중심 블록 기준 ±radius 범위의 블록들
                start_index = max(0, center_index - radius)
                end_index = center_index + radius + 1
                
                # 범위 내 모든 인덱스 추가
                all_indices.extend(range(start_index, end_index))
            
            # 중복 제거 및 정렬
            unique_indices = sorted(list(set(all_indices)))
            
            return unique_indices
            
        except Exception as e:
            print(f"    ⚠️ 체크포인트 반경 계산 실패: {str(e)}")
            return []
    
    def get_checkpoint_info(self, slot_id: str) -> Optional[Dict[str, Any]]:
        """체크포인트 정보 조회 (스레드 안전)"""
        with self._cache_lock:
            return self.checkpoint_cache.get(slot_id)
    
    def get_all_checkpoints(self) -> Dict[str, Dict[str, Any]]:
        """모든 체크포인트 정보 반환 (스레드 안전)"""
        with self._cache_lock:
            return self.checkpoint_cache.copy()
    
    def cleanup_old_checkpoints(self, max_age_hours: int = 24) -> int:
        """오래된 체크포인트 정리"""
        current_time = datetime.now()
        removed_count = 0
        
        slots_to_remove = []
        
        for slot_id, checkpoint in self.checkpoint_cache.items():
            try:
                created_time = datetime.fromisoformat(checkpoint["created_at"])
                age_hours = (current_time - created_time).total_seconds() / 3600
                
                if age_hours > max_age_hours:
                    slots_to_remove.append(slot_id)
                    
            except Exception:
                # 파싱 실패한 체크포인트도 제거
                slots_to_remove.append(slot_id)
        
        for slot_id in slots_to_remove:
            del self.checkpoint_cache[slot_id]
            removed_count += 1
        
        if removed_count > 0:
            print(f"    🧹 오래된 체크포인트 {removed_count}개 정리 완료")
        
        return removed_count
    
    def _cleanup_cache_by_size(self) -> int:
        """캐시 크기 제한을 위한 정리 (LRU 기반)"""
        if len(self.checkpoint_cache) < self.max_cache_size:
            return 0
        
        removed_count = 0
        target_size = int(self.max_cache_size * 0.8)  # 80%까지 줄임
        
        # 마지막 접근 시간 기준으로 정렬 (LRU)
        sorted_slots = sorted(
            self.checkpoint_cache.items(),
            key=lambda x: x[1].get("last_accessed", ""),
            reverse=False  # 오래된 것부터
        )
        
        # 오래된 것부터 제거
        for slot_id, _ in sorted_slots:
            if len(self.checkpoint_cache) <= target_size:
                break
            del self.checkpoint_cache[slot_id]
            removed_count += 1
        
        if removed_count > 0:
            print(f"    🧹 캐시 크기 제한으로 {removed_count}개 체크포인트 정리")
        
        return removed_count
    
    def get_stats(self) -> Dict[str, Any]:
        """체크포인트 관리 통계 반환"""
        cache_hit_rate = 0.0
        total_accesses = self.stats["cache_hits"] + self.stats["cache_misses"]
        
        if total_accesses > 0:
            cache_hit_rate = self.stats["cache_hits"] / total_accesses
        
        return {
            "checkpoints_active": len(self.checkpoint_cache),
            "checkpoints_created": self.stats["checkpoints_created"],
            "checkpoints_accessed": self.stats["checkpoints_accessed"],
            "cache_hit_rate": round(cache_hit_rate, 3),
            "total_ltm_blocks": sum(
                len(cp["ltm_blocks"]) for cp in self.checkpoint_cache.values()
            )
        }
    
    def _compute_context_hash(self, context: str) -> str:
        """컨텍스트 해시 계산"""
        return hashlib.md5(context.encode('utf-8')).hexdigest()[:16]
    
    def _calculate_semantic_distance(self, embedding1: List[float], embedding2: List[float]) -> float:
        """두 임베딩 간의 의미적 거리 계산"""
        try:
            # 입력 검증 강화
            if not embedding1 or not embedding2:
                return 1.0  # 최대 거리
            
            # 리스트인지 확인
            if not isinstance(embedding1, (list, tuple, np.ndarray)):
                print(f"    ⚠️ embedding1이 리스트가 아님: {type(embedding1)}")
                return 1.0
            
            if not isinstance(embedding2, (list, tuple, np.ndarray)):
                print(f"    ⚠️ embedding2가 리스트가 아님: {type(embedding2)}")
                return 1.0
            
            # numpy 배열로 변환
            vec1 = np.array(embedding1, dtype=float)
            vec2 = np.array(embedding2, dtype=float)
            
            # 벡터 크기가 다르면 최대 거리 반환
            if len(vec1) != len(vec2):
                return 1.0
            
            # 벡터가 비어있으면 최대 거리 반환
            if vec1.size == 0 or vec2.size == 0:
                return 1.0
            
            # 코사인 유사도 계산
            dot_product = np.dot(vec1, vec2)
            norm1 = np.linalg.norm(vec1)
            norm2 = np.linalg.norm(vec2)
            
            if norm1 == 0 or norm2 == 0:
                return 1.0
            
            cosine_similarity = dot_product / (norm1 * norm2)
            
            # 거리는 1 - 유사도
            distance = 1.0 - cosine_similarity
            
            return max(0.0, min(1.0, distance))  # 0-1 범위로 클램핑
            
        except Exception as e:
            print(f"    ⚠️ 의미적 거리 계산 실패: {str(e)}")
            return 1.0  # 오류 시 최대 거리 반환
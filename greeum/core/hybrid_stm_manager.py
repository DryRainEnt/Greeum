"""
Hybrid STM Manager - Phase 2+3 하이브리드 STM 구현

기존 STMManager와 새로운 WorkingMemoryManager를 통합하는 하이브리드 시스템
Phase 3에서 체크포인트 시스템과 연동됩니다.
"""

import time
import threading
from typing import List, Dict, Any, Optional
from datetime import datetime

from .stm_manager import STMManager
from .database_manager import DatabaseManager


class WorkingMemorySlot:
    """개별 작업 메모리 슬롯"""
    
    def __init__(self, slot_id: int):
        self.slot_id = slot_id
        
        # 컨텍스트 데이터 (요약 없이 원본 유지)
        self.context = ""
        self.content = None
        self.metadata = {}
        self.embedding = []          # Phase 3: 체크포인트 시스템용 임베딩
        
        # 우선순위 계산 요소들
        self.importance = 0.5        # 기본 중요도
        self.relevance_score = 0.0   # 현재 컨텍스트와의 연관성
        self.last_access = datetime.now()  # 최근 접근 시간
        self.usage_count = 0         # 사용 횟수
        self.created_at = datetime.now()   # 생성 시간
        
        # LTM 체크포인트 연결 (Phase 3)
        self.ltm_checkpoints = []    # 연결된 LTM 블록 좌표들
    
    def calculate_priority(self, current_context: str = "") -> float:
        """다차원 우선순위 계산"""
        time_factor = self._calculate_time_factor()     # 시간 가중치
        usage_factor = min(1.0, self.usage_count / 10)  # 사용빈도 가중치 (최대 10회)
        relevance_factor = self._calculate_relevance(current_context)  # 연관성 가중치
        
        priority = (
            self.importance * 0.4 +      # 중요도 40%
            time_factor * 0.3 +          # 시간 30%
            usage_factor * 0.2 +         # 사용빈도 20%
            relevance_factor * 0.1       # 연관성 10%
        )
        
        return max(0.0, min(1.0, priority))  # 0-1 범위 보장
    
    def _calculate_time_factor(self) -> float:
        """시간 기반 가중치 계산 (최근일수록 높음)"""
        now = datetime.now()
        access_hours = (now - self.last_access).total_seconds() / 3600
        
        # 24시간 이내: 1.0, 48시간: 0.5, 72시간: 0.25
        return max(0.1, 1.0 / (1 + access_hours / 24))
    
    def _calculate_relevance(self, current_context: str) -> float:
        """컨텍스트 연관성 계산 (간단한 키워드 매칭)"""
        if not current_context or not self.context:
            return 0.0
        
        # 간단한 키워드 매칭 기반 연관성
        current_words = set(current_context.lower().split())
        slot_words = set(self.context.lower().split())
        
        if not current_words or not slot_words:
            return 0.0
        
        intersection = current_words.intersection(slot_words)
        union = current_words.union(slot_words)
        
        return len(intersection) / len(union) if union else 0.0  # Jaccard 유사도
    
    def update_ltm_checkpoint(self, related_blocks: List[Dict[str, Any]]):
        """관련 LTM 블록들을 체크포인트로 저장"""
        self.ltm_checkpoints = [
            {
                "block_index": block["block_index"],
                "relevance": block.get("similarity_score", 0.5),
                "last_accessed": datetime.now().isoformat()
            }
            for block in related_blocks[:5]  # 상위 5개만 저장
        ]
    
    def get_checkpoint_blocks(self) -> List[int]:
        """체크포인트된 LTM 블록 인덱스 반환"""
        return [cp["block_index"] for cp in self.ltm_checkpoints]
    
    def access(self):
        """슬롯 접근 시 통계 업데이트"""
        self.usage_count += 1
        self.last_access = datetime.now()
    
    def clear(self):
        """슬롯 초기화"""
        self.context = ""
        self.content = None
        self.metadata = {}
        self.importance = 0.5
        self.relevance_score = 0.0
        self.usage_count = 0
        self.ltm_checkpoints = []
        self.created_at = datetime.now()
        self.last_access = datetime.now()
    
    def is_empty(self) -> bool:
        """슬롯이 비어있는지 확인"""
        return self.context == ""
    
    def to_dict(self) -> Dict[str, Any]:
        """슬롯 정보를 딕셔너리로 변환"""
        return {
            "slot_id": self.slot_id,
            "context": self.context,
            "content": self.content,
            "metadata": self.metadata,
            "importance": self.importance,
            "relevance_score": self.relevance_score,
            "usage_count": self.usage_count,
            "created_at": self.created_at.isoformat(),
            "last_access": self.last_access.isoformat(),
            "ltm_checkpoints": self.ltm_checkpoints
        }


class WorkingMemoryManager:
    """4슬롯 Working Memory 시스템"""
    
    def __init__(self, slots: int = 4, checkpoint_enabled: bool = True, smart_cleanup: bool = True):
        self.slots = [WorkingMemorySlot(i) for i in range(slots)]
        self.checkpoint_enabled = checkpoint_enabled
        self.smart_cleanup = smart_cleanup
        self._slot_lock = threading.RLock()  # 슬롯 접근 동시성 보장
        
        # 통계
        self.cleanup_count = 0
        self.promotion_count = 0
        self.total_additions = 0
        
        # 성능 추적
        self.last_cleanup_time = datetime.now()
        self.average_priority = 0.0
    
    def has_available_slot(self) -> bool:
        """사용 가능한 슬롯이 있는지 확인 (스레드 안전)"""
        with self._slot_lock:
            return any(slot.is_empty() for slot in self.slots)
    
    def get_active_slots(self) -> List[WorkingMemorySlot]:
        """활성 슬롯들 반환 (스레드 안전)"""
        with self._slot_lock:
            return [slot for slot in self.slots if not slot.is_empty()]
    
    def get_available_slots(self) -> List[WorkingMemorySlot]:
        """사용 가능한 슬롯들 반환 (스레드 안전)"""
        with self._slot_lock:
            return [slot for slot in self.slots if slot.is_empty()]
    
    def _get_available_slot_atomic(self) -> Optional[WorkingMemorySlot]:
        """원자적 슬롯 할당 (경합 상태 방지)"""
        # 락 내부에서만 호출되므로 추가 락 불필요
        for slot in self.slots:
            if slot.is_empty():
                return slot
        return None
    
    def add_memory(self, context: str, content: Any = None, metadata: Dict = None, importance: float = 0.5) -> bool:
        """Working Memory에 새 컨텍스트 추가 (스레드 안전)"""
        with self._slot_lock:
            self.total_additions += 1
            
            # 원자적 슬롯 할당
            available_slot = self._get_available_slot_atomic()
            if available_slot is not None:
                # 빈 슬롯에 추가
                self._populate_slot(available_slot, context, content, metadata, importance)
                return True
            else:
                # 공간 부족 시 지능적 정리
                if self.smart_cleanup:
                    victim_slot = self._find_least_important_slot(context)
                    if victim_slot:
                        self._promote_to_ltm(victim_slot)
                        self._populate_slot(victim_slot, context, content, metadata, importance)
                        self.cleanup_count += 1
                        self.last_cleanup_time = datetime.now()
                        return True
            
            return False
    
    def _populate_slot(self, slot: WorkingMemorySlot, context: str, content: Any, metadata: Dict, importance: float):
        """슬롯에 데이터 채우기"""
        slot.context = context
        slot.content = content
        slot.metadata = metadata or {}
        slot.importance = max(0.0, min(1.0, importance))  # 0-1 범위 보장
        slot.last_access = datetime.now()
        slot.usage_count = 1
        slot.created_at = datetime.now()
        slot.relevance_score = 0.0
        slot.ltm_checkpoints = []
    
    def _find_least_important_slot(self, current_context: str = "") -> Optional[WorkingMemorySlot]:
        """가장 낮은 우선순위 슬롯 찾기"""
        active_slots = self.get_active_slots()
        if not active_slots:
            return None
        
        # 우선순위 계산 후 가장 낮은 것 선택
        slot_priorities = [
            (slot, slot.calculate_priority(current_context)) 
            for slot in active_slots
        ]
        
        # 우선순위 업데이트
        priorities = [p[1] for p in slot_priorities]
        self.average_priority = sum(priorities) / len(priorities) if priorities else 0.0
        
        return min(slot_priorities, key=lambda x: x[1])[0]
    
    def _promote_to_ltm(self, slot: WorkingMemorySlot):
        """슬롯을 LTM으로 승격 (Phase 3에서 실제 구현 예정)"""
        # Phase 2에서는 단순히 로그만 남김
        self.promotion_count += 1
        print(f"[Working Memory] Promoting slot {slot.slot_id} to LTM: {slot.context[:50]}...")
        
        # 슬롯 클리어
        slot.clear()
    
    def search_working_memory(self, query_embedding: List[float] = None, current_context: str = "") -> List[Dict[str, Any]]:
        """Working Memory 내에서 검색"""
        results = []
        
        for slot in self.get_active_slots():
            # 컨텍스트 매칭 확인
            relevance = 0.0
            
            if current_context and slot.context:
                # 텍스트 매칭 기반 연관성
                if current_context.lower() in slot.context.lower():
                    relevance = slot.calculate_priority(current_context)
                else:
                    # 키워드 기반 연관성
                    relevance = slot._calculate_relevance(current_context)
            else:
                # 기본 우선순위 사용
                relevance = slot.calculate_priority()
            
            if relevance > 0.1:  # 최소 연관성 임계값
                results.append({
                    "slot_id": slot.slot_id,
                    "context": slot.context,
                    "content": slot.content,
                    "metadata": slot.metadata,
                    "relevance": relevance,
                    "priority": slot.calculate_priority(current_context),
                    "usage_count": slot.usage_count,
                    "source": "working_memory"
                })
                
                # 사용 카운트 증가
                slot.access()
        
        # 연관성 순으로 정렬
        return sorted(results, key=lambda x: x["relevance"], reverse=True)
    
    def get_statistics(self) -> Dict[str, Any]:
        """Working Memory 통계"""
        active_slots = self.get_active_slots()
        
        return {
            "total_slots": len(self.slots),
            "active_slots": len(active_slots),
            "available_slots": len(self.slots) - len(active_slots),
            "utilization_rate": len(active_slots) / len(self.slots),
            "cleanup_count": self.cleanup_count,
            "promotion_count": self.promotion_count,
            "total_additions": self.total_additions,
            "average_priority": self.average_priority,
            "cleanup_efficiency": self.cleanup_count / max(1, self.total_additions),
            "last_cleanup": self.last_cleanup_time.isoformat(),
            "slot_details": [slot.to_dict() for slot in active_slots]
        }


class HybridSTMManager:
    """기존 STM과 Working Memory를 통합하는 하이브리드 매니저"""
    
    def __init__(self, db_manager: DatabaseManager, mode: str = "hybrid"):
        # 기존 시스템 (호환성 보장)
        self.legacy_stm = STMManager(db_manager)
        
        # 새로운 Working Memory
        self.working_memory = WorkingMemoryManager(
            slots=4,
            checkpoint_enabled=True,
            smart_cleanup=True
        )
        
        # 동시성 보장
        self._hybrid_lock = threading.RLock()
        
        # 동작 모드
        self.mode = mode  # "hybrid" | "legacy" | "working_only"
        
        # 통계
        self.hybrid_stats = {
            "total_requests": 0,
            "working_memory_hits": 0,
            "legacy_stm_hits": 0,
            "combined_results": 0,
            "mode_switches": 0
        }
        
        # 성능 추적
        self.start_time = datetime.now()
        self.last_optimization = datetime.now()
    
    def add_memory(self, memory_data: Dict[str, Any]) -> Optional[str]:
        """메모리 추가 (모드에 따라 다르게 처리, 스레드 안전)"""
        with self._hybrid_lock:
            self.hybrid_stats["total_requests"] += 1
            
            if self.mode == "hybrid":
                # Working Memory 우선 시도
                context = memory_data.get("content", "")
                importance = memory_data.get("importance", 0.5)
                
                if self.working_memory.add_memory(context, memory_data, importance=importance):
                    self.hybrid_stats["working_memory_hits"] += 1
                    # 동시에 legacy STM에도 저장 (호환성)
                    legacy_id = self.legacy_stm.add_memory(memory_data)
                    return f"hybrid_{len(self.working_memory.get_active_slots())}_{legacy_id}"
                else:
                    # Working Memory 실패 시 legacy 사용
                    self.hybrid_stats["legacy_stm_hits"] += 1
                    return self.legacy_stm.add_memory(memory_data)
            
            elif self.mode == "working_only":
                context = memory_data.get("content", "")
                importance = memory_data.get("importance", 0.5)
                
                if self.working_memory.add_memory(context, memory_data, importance=importance):
                    self.hybrid_stats["working_memory_hits"] += 1
                    return f"working_{len(self.working_memory.get_active_slots())}"
                return None
            
            else:  # legacy mode
                self.hybrid_stats["legacy_stm_hits"] += 1
                return self.legacy_stm.add_memory(memory_data)
    
    def search_memories(self, query: str, query_embedding: List[float] = None, top_k: int = 5) -> List[Dict[str, Any]]:
        """통합 메모리 검색"""
        results = []
        
        if self.mode in ["hybrid", "working_only"]:
            # Working Memory 검색 - 임베딩이 없으면 생성
            if query_embedding is None:
                query_embedding = self._generate_query_embedding(query)
            wm_results = self.working_memory.search_working_memory(query_embedding, query)
            results.extend(wm_results)
            
            if wm_results:
                self.hybrid_stats["working_memory_hits"] += 1
        
        if self.mode in ["hybrid", "legacy"] and len(results) < top_k:
            # Legacy STM 검색 (부족한 만큼만)
            remaining = top_k - len(results)
            legacy_results = self.legacy_stm.get_recent_memories(remaining)
            
            # 결과 변환
            for legacy in legacy_results:
                results.append({
                    "context": legacy.get("content", ""),
                    "content": legacy,
                    "relevance": 0.3,  # 기본 연관성
                    "source": "legacy_stm"
                })
            
            if legacy_results:
                self.hybrid_stats["legacy_stm_hits"] += 1
        
        if len(results) > 0:
            self.hybrid_stats["combined_results"] += 1
        
        return results[:top_k]
    
    def search_working_memory(self, query_embedding: List[float]) -> List[Dict[str, Any]]:
        """Phase 3용: Working Memory 직접 검색"""
        if self.mode in ["hybrid", "working_only"]:
            return self.working_memory.search_working_memory(query_embedding, "")
        return []
    
    def get_recent_memories(self, count: int = 10) -> List[Dict[str, Any]]:
        """최근 메모리 조회 (기존 STM API 호환)"""
        if self.mode == "working_only":
            # Working Memory에서 활성 슬롯들을 최근 순으로 반환
            active_slots = self.working_memory.get_active_slots()
            
            # 최근 접근 시간 순으로 정렬
            sorted_slots = sorted(active_slots, key=lambda x: x.last_access, reverse=True)
            
            return [{
                "id": f"working_{slot.slot_id}",
                "content": slot.context,
                "timestamp": slot.last_access.isoformat(),
                "metadata": slot.metadata,
                "importance": slot.importance,
                "usage_count": slot.usage_count
            } for slot in sorted_slots[:count]]
        
        elif self.mode == "hybrid":
            # Working Memory + Legacy 결합 (무한 재귀 방지)
            # Working Memory에서 직접 가져오기
            active_slots = self.working_memory.get_active_slots()
            sorted_slots = sorted(active_slots, key=lambda x: x.last_access, reverse=True)
            wm_results = [{
                "id": f"working_{slot.slot_id}",
                "content": slot.context,
                "timestamp": slot.last_access.isoformat(),
                "metadata": slot.metadata,
                "importance": slot.importance,
                "usage_count": slot.usage_count
            } for slot in sorted_slots[:count//2]]
            
            legacy_results = self.legacy_stm.get_recent_memories(count - len(wm_results))
            
            all_results = wm_results + legacy_results
            return all_results[:count]
        
        else:  # legacy mode
            return self.legacy_stm.get_recent_memories(count)
    
    def switch_mode(self, new_mode: str) -> bool:
        """동작 모드 변경"""
        valid_modes = ["hybrid", "legacy", "working_only"]
        
        if new_mode in valid_modes:
            old_mode = self.mode
            self.mode = new_mode
            self.hybrid_stats["mode_switches"] += 1
            print(f"[Hybrid STM] Mode switched: {old_mode} → {new_mode}")
            return True
        
        return False
    
    def optimize_working_memory(self, current_context: str = ""):
        """Working Memory 최적화"""
        if self.mode in ["hybrid", "working_only"]:
            # 최적화 실행
            active_slots = self.working_memory.get_active_slots()
            
            # 모든 슬롯의 우선순위 재계산
            for slot in active_slots:
                slot.relevance_score = slot.calculate_priority(current_context)
            
            # 평균 우선순위 업데이트
            priorities = [slot.relevance_score for slot in active_slots]
            self.working_memory.average_priority = sum(priorities) / len(priorities) if priorities else 0.0
            
            # 매우 낮은 우선순위 슬롯 정리 (임계값 0.2 이하)
            low_priority_slots = [slot for slot in active_slots if slot.relevance_score < 0.2]
            
            for slot in low_priority_slots:
                if len(active_slots) > 2:  # 최소 2개 슬롯은 유지
                    self.working_memory._promote_to_ltm(slot)
                    active_slots.remove(slot)
            
            self.last_optimization = datetime.now()
    
    def get_hybrid_statistics(self) -> Dict[str, Any]:
        """하이브리드 시스템 통계"""
        wm_stats = self.working_memory.get_statistics()
        
        total_requests = max(1, self.hybrid_stats["total_requests"])
        
        return {
            "mode": self.mode,
            "working_memory": wm_stats,
            "hybrid_performance": self.hybrid_stats,
            "efficiency_metrics": {
                "working_memory_efficiency": self.hybrid_stats["working_memory_hits"] / total_requests,
                "legacy_stm_efficiency": self.hybrid_stats["legacy_stm_hits"] / total_requests,
                "combined_usage_rate": self.hybrid_stats["combined_results"] / total_requests,
                "mode_stability": 1.0 - (self.hybrid_stats["mode_switches"] / total_requests)
            },
            "system_uptime": (datetime.now() - self.start_time).total_seconds(),
            "last_optimization": self.last_optimization.isoformat()
        }
    
    def clear_all(self) -> int:
        """모든 메모리 클리어 (기존 STM API 호환)"""
        cleared_count = 0
        
        if self.mode in ["hybrid", "working_only"]:
            # Working Memory 클리어
            active_slots = len(self.working_memory.get_active_slots())
            for slot in self.working_memory.slots:
                slot.clear()
            cleared_count += active_slots
        
        if self.mode in ["hybrid", "legacy"]:
            # Legacy STM 클리어
            legacy_count = self.legacy_stm.clear_all()
            cleared_count += legacy_count
        
        return cleared_count
    
    def _generate_query_embedding(self, query: str) -> List[float]:
        """간단한 쿼리 임베딩 생성"""
        import hashlib
        
        # MD5 해시 기반 간단한 임베딩 생성
        hash_obj = hashlib.md5(query.encode('utf-8'))
        hash_hex = hash_obj.hexdigest()
        
        # 32자 hex를 16개 float로 변환 (0-15 → 0.0-1.0)
        embedding = []
        for i in range(0, len(hash_hex), 2):
            hex_pair = hash_hex[i:i+2]
            float_val = int(hex_pair, 16) / 255.0
            embedding.append(float_val)
        
        return embedding
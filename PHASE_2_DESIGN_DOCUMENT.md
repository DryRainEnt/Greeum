# Phase 2 설계서: 하이브리드 STM 시스템

**설계일**: 2025-08-02  
**목표**: F(38.7) → C(70+) 등급, 3배 성능 향상  
**브랜치**: phase2-hybrid-stm

---

## 🎯 설계 목표

### 📊 성능 목표
- **전체 등급**: F(38.7) → **C(70+)**
- **LTM 검색 시간**: 107ms → **50ms 이하**
- **지능적 메모리 관리**: 시간 기반 → **의미 기반**
- **API 호환성**: **100% 유지**

### 🏗️ 아키텍처 혁신
기존 TTL 기반 무제한 STM을 유지하면서, 새로운 **4슬롯 Working Memory** 시스템을 병행 도입합니다.

---

## 📋 핵심 설계

### 1️⃣ Working Memory 슬롯 구조
```python
class WorkingMemorySlot:
    """개별 작업 메모리 슬롯"""
    
    def __init__(self, slot_id: int):
        self.slot_id = slot_id
        
        # 컨텍스트 데이터 (요약 없이 원본 유지)
        self.context = ""
        self.content = None
        self.metadata = {}
        
        # 우선순위 계산 요소들
        self.importance = 0.5        # 기본 중요도
        self.relevance_score = 0.0   # 현재 컨텍스트와의 연관성
        self.last_access = datetime.now()  # 최근 접근 시간
        self.usage_count = 0         # 사용 횟수
        self.created_at = datetime.now()   # 생성 시간
        
        # LTM 체크포인트 연결
        self.ltm_checkpoints = []    # 연결된 LTM 블록 좌표들
    
    def calculate_priority(self, current_context: str = "") -> float:
        """다차원 우선순위 계산"""
        time_factor = self._calculate_time_factor()     # 시간 가중치
        usage_factor = min(1.0, self.usage_count / 10)  # 사용빈도 가중치
        relevance_factor = self._calculate_relevance(current_context)  # 연관성 가중치
        
        return (
            self.importance * 0.4 +      # 중요도 40%
            time_factor * 0.3 +          # 시간 30%
            usage_factor * 0.2 +         # 사용빈도 20%
            relevance_factor * 0.1       # 연관성 10%
        )
    
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
        
        return len(intersection) / len(union)  # Jaccard 유사도
    
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
```

### 2️⃣ Working Memory 매니저
```python
class WorkingMemoryManager:
    """4슬롯 Working Memory 시스템"""
    
    def __init__(self, slots: int = 4, checkpoint_enabled: bool = True, smart_cleanup: bool = True):
        self.slots = [WorkingMemorySlot(i) for i in range(slots)]
        self.checkpoint_enabled = checkpoint_enabled
        self.smart_cleanup = smart_cleanup
        
        # 통계
        self.cleanup_count = 0
        self.promotion_count = 0
    
    def has_available_slot(self) -> bool:
        """사용 가능한 슬롯이 있는지 확인"""
        return any(slot.context == "" for slot in self.slots)
    
    def get_active_slots(self) -> List[WorkingMemorySlot]:
        """활성 슬롯들 반환"""
        return [slot for slot in self.slots if slot.context != ""]
    
    def add_memory(self, context: str, content: Any = None, metadata: Dict = None, importance: float = 0.5) -> bool:
        """Working Memory에 새 컨텍스트 추가"""
        if self.has_available_slot():
            # 빈 슬롯에 추가
            for slot in self.slots:
                if slot.context == "":
                    self._populate_slot(slot, context, content, metadata, importance)
                    return True
        else:
            # 공간 부족 시 지능적 정리
            victim_slot = self._find_least_important_slot()
            if victim_slot:
                self._promote_to_ltm(victim_slot)
                self._populate_slot(victim_slot, context, content, metadata, importance)
                self.cleanup_count += 1
                return True
        
        return False
    
    def _populate_slot(self, slot: WorkingMemorySlot, context: str, content: Any, metadata: Dict, importance: float):
        """슬롯에 데이터 채우기"""
        slot.context = context
        slot.content = content
        slot.metadata = metadata or {}
        slot.importance = importance
        slot.last_access = datetime.now()
        slot.usage_count = 1
        slot.created_at = datetime.now()
    
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
        
        return min(slot_priorities, key=lambda x: x[1])[0]
    
    def _promote_to_ltm(self, slot: WorkingMemorySlot):
        """슬롯을 LTM으로 승격 (실제 구현은 Phase 3에서)"""
        # Phase 2에서는 단순히 로그만 남김
        self.promotion_count += 1
        print(f"[DEBUG] Promoting slot {slot.slot_id} to LTM: {slot.context[:50]}...")
    
    def search_working_memory(self, query_embedding: List[float], current_context: str = "") -> List[Dict[str, Any]]:
        """Working Memory 내에서 검색"""
        results = []
        
        for slot in self.get_active_slots():
            # 단순한 텍스트 매칭 (임시 구현)
            if current_context.lower() in slot.context.lower():
                relevance = slot.calculate_priority(current_context)
                results.append({
                    "slot_id": slot.slot_id,
                    "context": slot.context,
                    "content": slot.content,
                    "relevance": relevance,
                    "source": "working_memory"
                })
                
                # 사용 카운트 증가
                slot.usage_count += 1
                slot.last_access = datetime.now()
        
        # 연관성 순으로 정렬
        return sorted(results, key=lambda x: x["relevance"], reverse=True)
    
    def get_statistics(self) -> Dict[str, Any]:
        """Working Memory 통계"""
        active_slots = self.get_active_slots()
        
        return {
            "total_slots": len(self.slots),
            "active_slots": len(active_slots),
            "available_slots": len(self.slots) - len(active_slots),
            "cleanup_count": self.cleanup_count,
            "promotion_count": self.promotion_count,
            "average_priority": sum(slot.calculate_priority() for slot in active_slots) / len(active_slots) if active_slots else 0
        }
```

### 3️⃣ 하이브리드 STM 매니저
```python
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
        
        # 동작 모드
        self.mode = mode  # "hybrid" | "legacy" | "working_only"
        
        # 통계
        self.hybrid_stats = {
            "total_requests": 0,
            "working_memory_hits": 0,
            "legacy_stm_hits": 0,
            "combined_results": 0
        }
    
    def add_memory(self, memory_data: Dict[str, Any]) -> Optional[str]:
        """메모리 추가 (모드에 따라 다르게 처리)"""
        self.hybrid_stats["total_requests"] += 1
        
        if self.mode == "hybrid":
            # Working Memory 우선 시도
            context = memory_data.get("content", "")
            importance = memory_data.get("importance", 0.5)
            
            if self.working_memory.add_memory(context, memory_data, importance=importance):
                self.hybrid_stats["working_memory_hits"] += 1
                # 동시에 legacy STM에도 저장 (호환성)
                legacy_id = self.legacy_stm.add_memory(memory_data)
                return f"working_{len(self.working_memory.get_active_slots())}_{legacy_id}"
            else:
                # Working Memory 실패 시 legacy 사용
                self.hybrid_stats["legacy_stm_hits"] += 1
                return self.legacy_stm.add_memory(memory_data)
        
        elif self.mode == "working_only":
            context = memory_data.get("content", "")
            importance = memory_data.get("importance", 0.5)
            
            if self.working_memory.add_memory(context, memory_data, importance=importance):
                return f"working_{len(self.working_memory.get_active_slots())}"
            return None
        
        else:  # legacy mode
            return self.legacy_stm.add_memory(memory_data)
    
    def search_memories(self, query: str, query_embedding: List[float] = None, top_k: int = 5) -> List[Dict[str, Any]]:
        """통합 메모리 검색"""
        results = []
        
        if self.mode in ["hybrid", "working_only"]:
            # Working Memory 검색
            wm_results = self.working_memory.search_working_memory(query_embedding or [], query)
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
    
    def get_hybrid_statistics(self) -> Dict[str, Any]:
        """하이브리드 시스템 통계"""
        wm_stats = self.working_memory.get_statistics()
        
        return {
            "mode": self.mode,
            "working_memory": wm_stats,
            "hybrid_performance": self.hybrid_stats,
            "working_memory_efficiency": self.hybrid_stats["working_memory_hits"] / max(1, self.hybrid_stats["total_requests"]),
            "combined_usage_rate": self.hybrid_stats["combined_results"] / max(1, self.hybrid_stats["total_requests"])
        }
```

---

## 🔧 구현 계획

### 📋 Phase 2 단계별 구현
1. **기존 STM 분석** → Working Memory 구조 설계
2. **WorkingMemorySlot 구현** → 우선순위 계산 알고리즘
3. **WorkingMemoryManager 구현** → 4슬롯 관리 로직
4. **HybridSTMManager 구현** → 통합 인터페이스
5. **성능 테스트** → 목표 달성 검증

### 🎯 검증 기준
```python
def test_phase2_performance():
    # 목표: F(38.7) → C(70+)
    # Working Memory 효율성 > 70%
    # 전체 응답 시간 < 50ms
    # API 호환성 100%
```

---

## 📈 예상 효과

### 🚀 성능 개선
- **지능적 메모리 관리**: 시간 → 의미 기반 우선순위
- **빠른 컨텍스트 접근**: Working Memory 직접 검색
- **리소스 효율성**: 고정 4슬롯으로 예측 가능한 사용량

### 📊 정량적 목표
- **전체 등급**: F(38.7) → **C(70+)**
- **메모리 검색**: F(54.6) → **C(70+)**
- **Working Memory 효율성**: **70%+**

---

**설계 완료일**: 2025-08-02  
**다음 단계**: 구현 시작 (HybridSTMManager 클래스)
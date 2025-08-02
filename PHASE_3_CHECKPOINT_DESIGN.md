# Phase 3: 체크포인트 시스템 설계서

**설계일**: 2025-08-02  
**목표**: B+등급(82/100) → A등급(90+/100) 달성  
**핵심**: Working Memory ↔ LTM 간 지능적 체크포인트 연결

---

## 🎯 설계 목표

### 📊 현재 상황 분석
- **Phase 1+2 성과**: B+등급(82/100) 달성
- **주요 강점**: 캐시 535x 개선, Working Memory 100% 적중
- **개선 필요**: LTM 검색 시 전체 스캔으로 인한 지연

### 🚀 Phase 3 목표
- **성능 목표**: A등급(90+/100) 달성
- **검색 시간**: 현재 0.32ms → 0.15ms (2배 추가 개선)
- **지역성 활용**: Working Memory 컨텍스트 기반 LTM 좁은 범위 검색
- **캐시 효율성**: 체크포인트 기반 스마트 캐싱

---

## 🏗️ 핵심 아키텍처

### 1️⃣ **체크포인트 관리자**

```python
class CheckpointManager:
    """Working Memory와 LTM 간의 체크포인트 관리"""
    
    def __init__(self, db_manager, block_manager):
        self.db_manager = db_manager
        self.block_manager = block_manager
        self.checkpoint_cache = {}  # 메모리 내 캐시
        self.max_checkpoints_per_slot = 5  # 슬롯당 최대 체크포인트
        
    def create_checkpoint(self, working_memory_slot, related_blocks):
        """Working Memory 슬롯에 LTM 체크포인트 생성"""
        checkpoint_data = {
            "slot_id": working_memory_slot.slot_id,
            "context_hash": self._compute_context_hash(working_memory_slot.context),
            "ltm_blocks": [
                {
                    "block_index": block["block_index"],
                    "relevance_score": block.get("similarity_score", 0.5),
                    "distance": self._calculate_semantic_distance(
                        working_memory_slot.embedding, 
                        block["embedding"]
                    ),
                    "created_at": datetime.now().isoformat()
                }
                for block in related_blocks[:self.max_checkpoints_per_slot]
            ],
            "created_at": datetime.now().isoformat(),
            "last_accessed": datetime.now().isoformat()
        }
        
        # 메모리 내 캐시에 저장
        self.checkpoint_cache[working_memory_slot.slot_id] = checkpoint_data
        
        # 영구 저장 (선택적)
        self._persist_checkpoint(checkpoint_data)
        
        return checkpoint_data
        
    def update_checkpoint_access(self, slot_id):
        """체크포인트 접근 시간 업데이트"""
        if slot_id in self.checkpoint_cache:
            self.checkpoint_cache[slot_id]["last_accessed"] = datetime.now().isoformat()
            
    def get_checkpoint_radius(self, slot_id, radius=10):
        """체크포인트 주변 블록 인덱스 반환"""
        if slot_id not in self.checkpoint_cache:
            return []
            
        checkpoint = self.checkpoint_cache[slot_id]
        all_indices = []
        
        for block_data in checkpoint["ltm_blocks"]:
            center_index = block_data["block_index"]
            # 중심 블록 기준 ±radius 범위의 블록들
            start_index = max(0, center_index - radius)
            end_index = center_index + radius + 1
            all_indices.extend(range(start_index, end_index))
        
        return list(set(all_indices))  # 중복 제거
```

### 2️⃣ **지역 검색 엔진**

```python
class LocalizedSearchEngine:
    """체크포인트 기반 지역 검색"""
    
    def __init__(self, checkpoint_manager, block_manager):
        self.checkpoint_manager = checkpoint_manager
        self.block_manager = block_manager
        
    def search_with_checkpoints(self, query_embedding, working_memory, top_k=5):
        """체크포인트 기반 지역 검색"""
        localized_results = []
        
        # 1. Working Memory의 활성 슬롯들에서 체크포인트 수집
        active_slots = working_memory.get_active_slots()
        
        for slot in active_slots:
            # 슬롯과 쿼리의 관련성 계산
            slot_relevance = self._calculate_slot_relevance(
                slot.embedding, 
                query_embedding
            )
            
            # 관련성이 높은 슬롯만 사용 (임계값: 0.3)
            if slot_relevance > 0.3:
                checkpoint_indices = self.checkpoint_manager.get_checkpoint_radius(
                    slot.slot_id, 
                    radius=15  # 관련성에 따라 동적 조정 가능
                )
                
                # 2. 체크포인트 주변 블록들만 검색
                local_results = self._search_localized_blocks(
                    checkpoint_indices, 
                    query_embedding, 
                    top_k * 2  # 여유분 확보
                )
                
                # 슬롯 관련성으로 가중치 적용
                for result in local_results:
                    result["checkpoint_relevance"] = slot_relevance
                    result["source_slot"] = slot.slot_id
                
                localized_results.extend(local_results)
        
        # 3. 결과 통합 및 정렬
        if localized_results:
            # 중복 제거 (같은 블록 인덱스)
            unique_results = self._deduplicate_by_block_index(localized_results)
            
            # 종합 점수로 재정렬 (원래 점수 + 체크포인트 관련성)
            for result in unique_results:
                result["final_score"] = (
                    result.get("similarity_score", 0.5) * 0.7 +
                    result.get("checkpoint_relevance", 0.3) * 0.3
                )
            
            unique_results.sort(key=lambda x: x["final_score"], reverse=True)
            return unique_results[:top_k]
        
        # 4. 체크포인트 검색이 실패하면 전체 LTM 검색 (fallback)
        return self.block_manager.search_by_embedding(query_embedding, top_k)
        
    def _search_localized_blocks(self, block_indices, query_embedding, limit):
        """지정된 블록 인덱스들만 검색"""
        results = []
        
        for block_index in block_indices[:limit]:  # 검색 범위 제한
            try:
                block = self.block_manager.get_block_by_index(block_index)
                if block and "embedding" in block:
                    similarity = self._calculate_cosine_similarity(
                        query_embedding, 
                        block["embedding"]
                    )
                    
                    if similarity > 0.2:  # 최소 관련성 임계값
                        results.append({
                            "block_index": block_index,
                            "similarity_score": similarity,
                            "content": block.get("context", ""),
                            "keywords": block.get("keywords", [])
                        })
            except Exception:
                continue  # 블록 접근 실패 시 건너뛰기
                
        return sorted(results, key=lambda x: x["similarity_score"], reverse=True)
```

### 3️⃣ **통합 검색 조정자**

```python
class PhaseThreeSearchCoordinator:
    """Phase 3 검색 시스템 통합 조정"""
    
    def __init__(self, hybrid_stm, cache_manager, checkpoint_manager, localized_engine):
        self.hybrid_stm = hybrid_stm
        self.cache_manager = cache_manager
        self.checkpoint_manager = checkpoint_manager
        self.localized_engine = localized_engine
        
    def intelligent_search(self, user_input, query_embedding, keywords):
        """Phase 3 지능적 다층 검색"""
        search_start = time.perf_counter()
        
        # Layer 1: Working Memory 직접 검색 (가장 빠름)
        wm_results = self.hybrid_stm.search_working_memory(query_embedding)
        if len(wm_results) >= 3:
            self._update_checkpoints_on_success(wm_results)
            return self._format_results(wm_results, "working_memory", search_start)
        
        # Layer 2: 캐시 확인 (두 번째로 빠름)
        cached_results = self.cache_manager.get_cached_results(query_embedding, keywords)
        if cached_results:
            return self._format_results(cached_results, "cache", search_start)
        
        # Layer 3: 체크포인트 기반 지역 검색 (핵심 기능)
        checkpoint_results = self.localized_engine.search_with_checkpoints(
            query_embedding, 
            self.hybrid_stm.working_memory
        )
        
        if len(checkpoint_results) >= 2:
            # 성공적인 체크포인트 검색 시 캐시에 저장
            self.cache_manager.update_cache(
                user_input, query_embedding, keywords, checkpoint_results
            )
            return self._format_results(checkpoint_results, "checkpoint", search_start)
        
        # Layer 4: 전체 LTM 검색 (fallback)
        ltm_results = self.block_manager.search_by_embedding(query_embedding, top_k=5)
        
        # fallback 결과도 캐시에 저장
        self.cache_manager.update_cache(
            user_input, query_embedding, keywords, ltm_results
        )
        
        return self._format_results(ltm_results, "ltm_fallback", search_start)
        
    def _update_checkpoints_on_success(self, wm_results):
        """Working Memory 성공 시 체크포인트 업데이트"""
        for result in wm_results:
            slot_id = result.get("source_slot")
            if slot_id:
                self.checkpoint_manager.update_checkpoint_access(slot_id)
                
    def _format_results(self, results, source, start_time):
        """검색 결과 포맷팅"""
        search_time = (time.perf_counter() - start_time) * 1000  # ms
        
        return {
            "results": results,
            "source": source,
            "search_time_ms": round(search_time, 3),
            "result_count": len(results)
        }
```

---

## 📈 예상 성능 개선

### 🎯 **성능 목표**
- **현재**: 0.32ms 평균 → **목표**: 0.15ms (2배 개선)
- **체크포인트 적중률**: 70%+ (Working Memory 컨텍스트 기반)
- **전체 성능 등급**: B+(82) → A(90+)

### 📊 **계층별 성능 예상**
1. **Working Memory**: 0.045ms (기존 유지)
2. **캐시 히트**: 0.08ms (기존 유지)  
3. **체크포인트 검색**: **0.12ms** (신규, LTM 전체 대비 5-10배 빠름)
4. **LTM 전체**: 0.67ms (fallback)

### 🚀 **체크포인트 효과**
- **검색 범위**: 전체 LTM → Working Memory 관련 지역만
- **검색 속도**: 5-10배 향상 예상
- **관련성**: 컨텍스트 기반으로 더 높은 정확도

---

## ✅ 검증 계획

### 🧪 **단위 테스트**
```python
def test_checkpoint_creation():
    """체크포인트 생성 테스트"""
    # Working Memory 슬롯에 체크포인트 생성
    # 관련 LTM 블록들과 연결 확인
    # 메모리 내 캐시 저장 확인

def test_localized_search_performance():
    """지역 검색 성능 테스트"""
    # 1000개 블록 환경에서 체크포인트 vs 전체 검색 비교
    # 5-10배 속도 향상 확인
    # 관련성 점수 비교

def test_checkpoint_fallback():
    """체크포인트 실패 시 fallback 테스트"""
    # 체크포인트 없는 상황에서 전체 LTM 검색 확인
    # 성능 저하 없이 결과 반환 확인
```

### 📊 **성능 벤치마크**
```python
def benchmark_phase3_performance():
    """Phase 3 전체 성능 벤치마크"""
    # 100회 검색 테스트
    # 체크포인트 적중률 측정
    # 평균 응답 시간 측정
    # A등급(90+) 달성 확인
```

---

## 🛡️ 안전장치

### ⚙️ **설정 토글**
```python
class PhaseThreeConfig:
    CHECKPOINT_ENABLED = False  # Phase 3 활성화 토글
    CHECKPOINT_RADIUS = 15      # 검색 반경 조정
    MIN_RELEVANCE_THRESHOLD = 0.3  # 관련성 최소 임계값
    MAX_CHECKPOINTS_PER_SLOT = 5   # 슬롯당 최대 체크포인트
    LOCALIZED_SEARCH_LIMIT = 100   # 지역 검색 최대 블록 수
```

### 🔄 **점진적 활성화**
1. **1단계**: 체크포인트 생성만 활성화 (검색 사용 안함)
2. **2단계**: 지역 검색 활성화 (fallback과 병행)
3. **3단계**: 완전 활성화 (모든 기능 사용)

---

## 📋 구현 순서

### **Day 1**: 체크포인트 관리자 구현
- CheckpointManager 클래스 구현
- Working Memory 슬롯과 LTM 연결
- 메모리 내 캐시 구현

### **Day 2**: 지역 검색 엔진 구현  
- LocalizedSearchEngine 클래스 구현
- 체크포인트 기반 검색 로직
- 관련성 계산 알고리즘

### **Day 3**: 통합 및 테스트
- PhaseThreeSearchCoordinator 구현
- 단위 테스트 및 성능 벤치마크
- A등급 달성 확인

---

**설계 책임자**: Claude Code  
**설계 완료일**: 2025-08-02  
**구현 예정일**: 2025-08-03 ~ 2025-08-05  

*이 설계서는 Phase 1+2의 성공을 바탕으로 A등급 달성을 위한 체크포인트 시스템의 상세 구현 방안을 제시합니다.*
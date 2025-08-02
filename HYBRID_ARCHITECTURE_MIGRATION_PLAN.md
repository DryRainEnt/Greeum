# Greeum v2.0.5 하이브리드 점진적 개편 계획

## 🎯 전체 목표

현재 구조의 안정성을 유지하면서 새로운 STM/LTM 아키텍처를 점진적으로 도입하여 성능을 단계적으로 개선합니다.

### 📊 현재 성능 기준점 (2025-08-02 측정)
- **전체 성능 등급**: F (21.9/100)
- **LTM 검색 시간**: 108.94ms (목표: 10-20ms)
- **캐시 검색 시간**: 234.52ms (역설적으로 LTM보다 느림)
- **속도 향상 비율**: 0.54x (캐시가 더 느림)

### 🎯 최종 목표
- **전체 성능 등급**: A+ (90+/100)
- **검색 시간**: 10-20ms (현재 대비 5-10배 개선)
- **캐시 효율성**: 진정한 속도 향상 달성
- **안정성**: 기존 API 호환성 100% 유지

---

## 📋 Phase 1: 즉시 성능 개선 (1-2일)

### 🎯 목표
현재 캐시 시스템의 성능 문제를 해결하여 즉시 개선 효과를 달성합니다.

### 🔍 문제 분석
```python
# 현재 문제: CacheManager.update_cache()에서 중복 검색 수행
def update_cache(self, user_input, query_embedding, keywords, top_k=5):
    # 키워드 검색 + 임베딩 검색 모두 수행 → 중복 오버헤드
    keyword_results = self.block_manager.search_by_keywords(keywords)     # 검색 1
    embedding_results = self.block_manager.search_by_embedding(embedding) # 검색 2
    # 결과 병합 로직도 복잡 → 추가 오버헤드
```

### 🔧 개선 방안
```python
class OptimizedCacheManager:
    def __init__(self, cache_ttl=300):  # 5분 캐시
        self.cache = {}
        self.cache_ttl = cache_ttl
    
    def update_cache(self, user_input, query_embedding, keywords, top_k=5):
        # 1. 캐시 검사
        cache_key = self._compute_cache_key(query_embedding)
        cached_result = self._get_cached_result(cache_key)
        if cached_result:
            return cached_result  # 즉시 반환
        
        # 2. 단일 임베딩 검색만 수행
        results = self.block_manager.search_by_embedding(query_embedding, top_k)
        
        # 3. 캐시 저장
        self._cache_result(cache_key, results)
        return results
    
    def _compute_cache_key(self, embedding):
        """임베딩 기반 캐시 키 생성"""
        return hashlib.md5(str(embedding[:10]).encode()).hexdigest()[:8]
```

### 📈 예상 효과
- **캐시 검색 시간**: 234.52ms → 50ms (5배 개선)
- **전체 성능**: F등급 → D등급 예상
- **즉시 효과**: 모든 기존 코드에서 체감 가능한 성능 향상

### ✅ 검증 방법
```bash
# Phase 1 완료 후 성능 테스트 실행
python3 tests/performance_suite/core/practical_performance_test.py

# 검증 기준:
# - 캐시 검색 시간 < 60ms
# - 전체 성능 등급 D 이상
# - 기존 API 호환성 100%
```

---

## 📋 Phase 2: 하이브리드 STM 도입 (3-4일)

### 🎯 목표
기존 STM을 유지하면서 새로운 Working Memory 시스템을 병행 도입합니다.

### 🏗️ 아키텍처 설계
```python
class HybridSTMManager:
    def __init__(self, db_manager):
        # 기존 시스템 (호환성 보장)
        self.legacy_stm = STMManager(db_manager)
        
        # 새로운 Working Memory
        self.working_memory = WorkingMemoryManager(
            slots=4,                    # 3-4개 고정 슬롯
            checkpoint_enabled=True,    # LTM 체크포인트 연결
            smart_cleanup=True          # 지능적 정리
        )
        
        # 동작 모드
        self.mode = "hybrid"  # hybrid | legacy | working_only
    
    def add_memory(self, memory_data):
        if self.mode == "hybrid":
            # Working Memory 우선 시도
            if self.working_memory.has_available_slot():
                return self._add_to_working_memory(memory_data)
            else:
                # 공간 부족 시 지능적 정리 후 추가
                self._promote_least_important()
                return self._add_to_working_memory(memory_data)
        else:
            # 기존 방식 사용
            return self.legacy_stm.add_memory(memory_data)

class WorkingMemorySlot:
    def __init__(self, slot_id):
        self.slot_id = slot_id
        self.context = ""
        self.content = None
        self.metadata = {}
        
        # 우선순위 계산 요소들
        self.importance = 0.5
        self.relevance_score = 0.0
        self.last_access = datetime.now()
        self.usage_count = 0
        self.created_at = datetime.now()
        
        # LTM 연결
        self.ltm_checkpoints = []
    
    def calculate_priority(self, current_context=""):
        """다차원 우선순위 계산"""
        time_factor = self._calculate_time_factor()
        usage_factor = min(1.0, self.usage_count / 10)
        relevance_factor = self._calculate_relevance(current_context)
        
        return (
            self.importance * 0.4 + 
            time_factor * 0.3 + 
            usage_factor * 0.2 + 
            relevance_factor * 0.1
        )
```

### 📈 예상 효과
- **지능적 STM 관리**: 의미 기반 정리로 더 관련성 높은 기억 유지
- **메모리 효율성**: 고정 슬롯으로 예측 가능한 리소스 사용
- **전체 성능**: D등급 → C등급 예상

### ✅ 검증 방법
```python
# Working Memory 동작 테스트
def test_working_memory_intelligence():
    wm = WorkingMemoryManager(slots=4)
    
    # 4개 슬롯 채우기
    for i in range(4):
        wm.add_memory(f"테스트 컨텍스트 {i}")
    
    # 5번째 추가 시 지능적 정리 확인
    wm.add_memory("새로운 중요한 컨텍스트")
    
    # 검증: 가장 낮은 우선순위가 제거되었는가?
    assert len(wm.get_active_slots()) == 4
    assert "새로운 중요한 컨텍스트" in wm.get_contexts()
```

---

## 📋 Phase 3: 체크포인트 시스템 구축 (2-3일)

### 🎯 목표
Working Memory와 LTM 간의 체크포인트 연결을 구축하여 지역성 기반 빠른 검색을 구현합니다.

### 🔧 체크포인트 시스템
```python
class WorkingMemorySlot:
    def update_ltm_checkpoint(self, related_blocks):
        """관련 LTM 블록들을 체크포인트로 저장"""
        self.ltm_checkpoints = [
            {
                "block_index": block["block_index"],
                "relevance": block.get("similarity_score", 0.5),
                "last_accessed": datetime.now().isoformat()
            }
            for block in related_blocks[:5]  # 상위 5개만 저장
        ]
    
    def get_checkpoint_blocks(self):
        """체크포인트된 LTM 블록 좌표 반환"""
        return [cp["block_index"] for cp in self.ltm_checkpoints]

class CheckpointSearchEngine:
    def search_with_checkpoints(self, query_embedding, working_memory):
        """체크포인트 기반 지역 검색"""
        results = []
        
        # 1. Working Memory 슬롯들의 체크포인트 확인
        for slot in working_memory.get_active_slots():
            checkpoint_blocks = slot.get_checkpoint_blocks()
            
            # 2. 체크포인트 주변 블록들만 검색 (반경 10블록)
            local_results = self._search_around_blocks(
                checkpoint_blocks, 
                query_embedding, 
                radius=10
            )
            results.extend(local_results)
        
        # 3. 중복 제거 및 점수 순 정렬
        unique_results = self._deduplicate_by_block_index(results)
        
        # 4. 충분한 결과가 없으면 전체 LTM 검색 (fallback)
        if len(unique_results) < 3:
            fallback_results = self.block_manager.search_by_embedding(
                query_embedding, top_k=5
            )
            unique_results.extend(fallback_results)
        
        return unique_results[:5]  # 상위 5개 반환
```

### 📈 예상 효과
- **검색 속도**: 전체 LTM 대신 지역 검색으로 5-10배 향상
- **관련성**: 체크포인트 기반으로 더 맥락적으로 관련된 결과
- **전체 성능**: C등급 → B등급 예상

### ✅ 검증 방법
```python
def test_checkpoint_performance():
    # 1000개 블록 환경에서 체크포인트 vs 전체 검색 비교
    setup_test_blocks(1000)
    
    # 체크포인트 검색 시간 측정
    start = time.perf_counter()
    checkpoint_results = checkpoint_engine.search_with_checkpoints(query_embedding, wm)
    checkpoint_time = time.perf_counter() - start
    
    # 전체 검색 시간 측정
    start = time.perf_counter()
    full_results = block_manager.search_by_embedding(query_embedding)
    full_time = time.perf_counter() - start
    
    # 검증: 체크포인트가 더 빠르고 관련성도 높은가?
    assert checkpoint_time < full_time * 0.5  # 2배 이상 빠름
    assert calculate_relevance(checkpoint_results) >= calculate_relevance(full_results)
```

---

## 📋 Phase 4: 최적화 검색 활용 (1-2일)

### 🎯 목표
모든 구성요소를 통합하여 최적화된 검색 시스템을 완성합니다.

### 🚀 통합 검색 시스템
```python
class OptimizedGreeumSearchEngine:
    def __init__(self, hybrid_stm, optimized_cache, checkpoint_engine):
        self.hybrid_stm = hybrid_stm
        self.cache = optimized_cache
        self.checkpoint_engine = checkpoint_engine
    
    def intelligent_search(self, query, query_embedding):
        """지능적 다층 검색"""
        
        # Layer 1: Working Memory 직접 검색
        wm_results = self.hybrid_stm.search_working_memory(query_embedding)
        if self._is_sufficient(wm_results):
            return wm_results
        
        # Layer 2: 캐시된 결과 확인
        cached_results = self.cache.get_cached_results(query_embedding)
        if cached_results:
            return cached_results
        
        # Layer 3: 체크포인트 기반 지역 검색
        checkpoint_results = self.checkpoint_engine.search_with_checkpoints(
            query_embedding, 
            self.hybrid_stm.working_memory
        )
        
        # Layer 4: 필요시에만 전체 LTM 검색 (fallback)
        if len(checkpoint_results) < 3:
            ltm_results = self.block_manager.search_by_embedding(query_embedding)
            checkpoint_results.extend(ltm_results)
        
        # 결과 캐싱
        final_results = self._merge_and_rank(checkpoint_results)
        self.cache.cache_results(query_embedding, final_results)
        
        return final_results
```

### 📈 예상 효과
- **최종 성능**: 108ms → 10-20ms (5-10배 개선)
- **전체 등급**: B등급 → A등급 예상
- **사용자 경험**: 체감 가능한 반응 속도 향상

### ✅ 최종 검증
```bash
# 전체 시스템 성능 테스트
python3 tests/performance_suite/core/practical_performance_test.py

# 목표 달성 기준:
# - 전체 성능 등급: A 이상 (85+/100)
# - LTM 검색 평균: < 25ms
# - 캐시 검색 평균: < 15ms
# - 속도 향상 비율: > 3.0x
```

---

## 🔄 진행 방식

### 📋 각 Phase별 진행 절차
1. **설계 및 구현** → 2. **단위 테스트** → 3. **성능 검증** → 4. **커밋** → 5. **다음 Phase**

### ✅ 커밋 기준
각 Phase는 다음 조건을 모두 만족할 때만 커밋합니다:
- [ ] 의도한 성능 개선 효과 달성
- [ ] 기존 API 호환성 100% 유지
- [ ] 단위 테스트 모두 통과
- [ ] 성능 테스트로 개선 효과 검증

### 🛡️ 안전장치
```python
# 설정을 통한 점진적 활성화
class GreeumConfig:
    # Phase별 기능 토글
    OPTIMIZED_CACHE_ENABLED = False      # Phase 1
    HYBRID_STM_ENABLED = False           # Phase 2  
    CHECKPOINT_SEARCH_ENABLED = False    # Phase 3
    INTELLIGENT_SEARCH_ENABLED = False   # Phase 4
    
    # 안전장치
    LEGACY_FALLBACK_ENABLED = True       # 항상 True
    PERFORMANCE_MONITORING = True        # 항상 True

# 각 Phase 완료 시 해당 기능만 활성화
# 문제 발생 시 즉시 비활성화 가능
```

---

## 📊 예상 타임라인

| Phase | 기간 | 누적 개선 | 검증 포인트 |
|-------|------|----------|-------------|
| Phase 1 | 1-2일 | 2배 빠름 | 캐시 < 60ms |
| Phase 2 | 3-4일 | 3배 빠름 | STM 지능적 정리 확인 |
| Phase 3 | 2-3일 | 5배 빠름 | 체크포인트 검색 < 30ms |
| Phase 4 | 1-2일 | 10배 빠름 | 전체 < 25ms |
| **총계** | **7-11일** | **10배 성능 향상** | **A등급 달성** |

---

## 🎯 성공 지표

### 📈 정량적 목표
- **전체 성능 등급**: F(21.9) → A(85+)
- **검색 응답 시간**: 108ms → 10-20ms
- **캐시 효율성**: 0.54x → 5.0x+
- **API 호환성**: 100% 유지

### 📋 정성적 목표
- **개발자 경험**: 기존 코드 수정 없이 성능 향상 체감
- **시스템 안정성**: 단계별 검증으로 리스크 최소화
- **확장성**: 새로운 아키텍처 기반으로 향후 발전 가능

---

**문서 작성일**: 2025-08-02  
**최종 업데이트**: Phase 진행에 따라 지속 업데이트  
**책임자**: Claude Code + 사용자 협업
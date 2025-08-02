# Critical STM Issues - 즉시 수정 필요

## 🚨 발견된 Critical 이슈들

### 1️⃣ Working Memory 검색 실패 (search_memories)
**문제**: `query_embedding or []` → 항상 빈 리스트 전달
**위치**: `greeum/core/hybrid_stm_manager.py:342`
**영향**: Working Memory 검색 적중률 0%

**현재 코드**:
```python
def search_memories(self, query: str, query_embedding: List[float] = None, top_k: int = 5):
    if self.mode in ["hybrid", "working_only"]:
        wm_results = self.working_memory.search_working_memory(query_embedding or [], query)
        # 😱 빈 리스트 전달!
```

**수정 방안**:
```python
def search_memories(self, query: str, query_embedding: List[float] = None, top_k: int = 5):
    if self.mode in ["hybrid", "working_only"]:
        # query_embedding이 None이면 기본 임베딩 생성
        if query_embedding is None:
            query_embedding = self._generate_query_embedding(query)
        wm_results = self.working_memory.search_working_memory(query_embedding, query)
```

### 2️⃣ 무한 재귀 호출 (get_recent_memories)
**문제**: hybrid 모드에서 자기 자신 호출
**위치**: `greeum/core/hybrid_stm_manager.py:390`
**영향**: 스택 오버플로우 위험

**현재 코드**:
```python
elif self.mode == "hybrid":
    wm_results = self.get_recent_memories(count // 2)  # 😱 무한 재귀!
```

**수정 방안**:
```python
elif self.mode == "hybrid":
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
```

### 3️⃣ Working Memory 활용도 부족
**문제**: 4슬롯 시스템의 효과적 활용 부족
**원인**: 검색 임베딩 부재, 컨텍스트 매칭 알고리즘 미흡

**수정 방안**:
```python
def _generate_query_embedding(self, query: str) -> List[float]:
    """간단한 쿼리 임베딩 생성"""
    # 문자 기반 간단한 임베딩 (실제로는 BERT 등 사용)
    import hashlib
    hash_obj = hashlib.md5(query.encode())
    hash_hex = hash_obj.hexdigest()
    
    # 32자 hex를 32개 float로 변환 (0-15 → 0.0-1.0)
    embedding = []
    for i in range(0, len(hash_hex), 2):
        hex_pair = hash_hex[i:i+2]
        float_val = int(hex_pair, 16) / 255.0
        embedding.append(float_val)
    
    return embedding
```

## 🔧 수정 우선순위

### Critical (즉시 수정)
1. **무한 재귀 호출** - 시스템 크래시 방지
2. **빈 임베딩 문제** - Working Memory 활성화

### High (24시간 내)
3. **Working Memory 효율성** - 실제 성능 향상

## 📊 예상 효과

**수정 전**:
- STM 적중률: 0%
- Working Memory 활용도: 0%

**수정 후 예상**:
- STM 적중률: 60-80%
- Working Memory 활용도: 70%+
- 전체 성능: B+ → A- 등급

## ⚠️ 긴급성

이 이슈들은 **Phase 2의 핵심 가치를 완전히 무효화**시키는 Critical 이슈입니다.
- Working Memory가 전혀 작동하지 않음
- 1500x 속도 향상이 실제로는 달성되지 않음
- 하이브리드 STM 시스템이 Legacy STM과 동일하게 동작

**즉시 수정이 필요합니다!**
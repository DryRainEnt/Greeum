# Greeum v3.0.0: AI 기반 마이그레이션 전략
## 완전히 새로운 데이터베이스로의 전환

---

## 🔄 **제안된 아키텍처**

```
v2.6.4 (Legacy)          →  AI 추론/해석  →      v3.0.0 (New)
━━━━━━━━━━━━━━━━           ━━━━━━━━━━━━           ━━━━━━━━━━━━━
기존 메모리 블록              Claude/LLM             액탄트 구조화
자유 텍스트 형식             의미 파싱              정형 데이터
context 필드만               관계 추론              6-actant model
━━━━━━━━━━━━━━━━           ━━━━━━━━━━━━           ━━━━━━━━━━━━━
```

---

## ⚖️ **트레이드오프 분석**

### 1. **얻는 것 (Gains)**

#### ✅ 정확도
- **자유로운 재해석**: AI가 전체 문맥을 보고 판단
- **암묵적 정보 추론**: 생략된 주어/목적어 보완
- **관계 발견**: 여러 메모리 간 숨은 연결고리 파악
- **일관성**: 모든 데이터가 동일한 AI 모델로 처리

#### ✅ 유연성
- **반복 가능**: 마이그레이션 실패시 재시도 가능
- **점진적 개선**: AI 모델 업그레이드시 재처리 가능
- **선택적 마이그레이션**: 중요한 메모리부터 우선 처리

#### ✅ 품질
- **의미 보존**: 단순 파싱이 아닌 의미 이해 기반
- **컨텍스트 활용**: 주변 메모리들과의 관계 고려
- **메타데이터 강화**: AI가 추가 정보 생성 가능

### 2. **잃는 것 (Losses)**

#### ❌ 비용
- **API 비용**: 247개 메모리 × $0.01 ≈ $2.47 (초기)
- **일일 운영**: 50개/일 × $0.01 ≈ $0.50/일
- **월 비용**: ~$15-20 예상

#### ❌ 속도
- **초기 마이그레이션**: 2-3시간 소요 (Rate limit)
- **실시간 처리**: 각 메모리당 1-2초 지연
- **배치 처리 필요**: API 제한으로 인한 대기

#### ❌ 의존성
- **인터넷 연결 필수**: 오프라인 작동 불가
- **API 안정성**: 서비스 장애시 기능 정지
- **모델 변경 리스크**: GPT/Claude 동작 변경시 영향

#### ❌ 제어권
- **결정론적이지 않음**: 같은 입력도 다른 결과 가능
- **디버깅 어려움**: AI 판단 과정 불투명
- **수정 제한**: 파싱 로직 직접 수정 불가

---

## 🛠️ **보완 방안**

### 1. **하이브리드 접근**

```python
class HybridMemorySystem:
    """v2.6.4와 v3.0.0 동시 운영"""
    
    def __init__(self):
        self.legacy_db = "data/memory.db"      # 원본 보존
        self.new_db = "data/memory_v3.db"      # 새 구조
        self.cache_db = "data/memory_cache.db" # 파싱 캐시
    
    async def get_memory(self, memory_id: int):
        # 1. v3.0.0에서 먼저 조회
        v3_memory = self.get_from_v3(memory_id)
        if v3_memory:
            return v3_memory
        
        # 2. 없으면 v2.6.4에서 조회
        v2_memory = self.get_from_legacy(memory_id)
        if not v2_memory:
            return None
        
        # 3. AI 파싱 (캐시 확인)
        if cached := self.get_from_cache(memory_id):
            return cached
        
        # 4. 새로 파싱하고 캐시
        parsed = await self.ai_parse(v2_memory)
        self.save_to_cache(memory_id, parsed)
        
        return parsed
```

### 2. **점진적 마이그레이션**

```python
class ProgressiveMigration:
    """우선순위 기반 단계적 마이그레이션"""
    
    phases = [
        # Phase 1: 최근 30일 메모리
        {"filter": "recent_days", "value": 30},
        
        # Phase 2: 중요도 0.7 이상
        {"filter": "importance", "value": 0.7},
        
        # Phase 3: 자주 접근하는 메모리
        {"filter": "access_count", "value": 5},
        
        # Phase 4: 나머지
        {"filter": "remaining", "value": None}
    ]
```

### 3. **폴백 메커니즘**

```python
class FallbackSystem:
    """AI 실패시 대체 방안"""
    
    async def parse_memory(self, text: str):
        try:
            # 1차: AI 파싱
            return await self.ai_parse(text)
        except AIUnavailable:
            # 2차: 로컬 개선 파서
            return self.local_parse_v2(text)
        except:
            # 3차: 기본 구조만
            return {
                "subject": None,
                "action": None,
                "object": text,  # 전체를 object로
                "confidence": 0.1
            }
```

### 4. **품질 검증 시스템**

```python
class QualityValidator:
    """AI 파싱 결과 검증"""
    
    def validate_parsing(self, original: str, parsed: Dict) -> bool:
        # 1. 정보 손실 체크
        if not self.contains_key_info(original, parsed):
            return False
        
        # 2. 논리적 일관성
        if not self.is_logically_consistent(parsed):
            return False
        
        # 3. 신뢰도 임계값
        if parsed.get('confidence', 0) < 0.5:
            return False
        
        return True
    
    def human_review_needed(self, parsed: Dict) -> bool:
        """인간 검토 필요 여부"""
        return (
            parsed['confidence'] < 0.7 or
            parsed['subject'] is None or
            'ambiguous' in parsed.get('metadata', {})
        )
```

---

## 📋 **구현 체크리스트**

### Phase 1: 기반 구축 (Week 1)
- [ ] v3.0.0 전용 데이터베이스 생성
- [ ] AI 파싱 인터페이스 구현
- [ ] 캐싱 시스템 구축
- [ ] 폴백 메커니즘

### Phase 2: 마이그레이션 도구 (Week 2)
- [ ] 배치 마이그레이션 스크립트
- [ ] 진행상황 모니터링
- [ ] 검증 도구
- [ ] 롤백 기능

### Phase 3: 실시간 처리 (Week 3)
- [ ] 새 메모리 자동 파싱
- [ ] MCP 도구 통합
- [ ] 실시간 폴백
- [ ] 성능 최적화

---

## 🎯 **핵심 결정 사항**

### 1. **데이터베이스 전략**
```
옵션 A: 완전 분리 (권장)
- v2.6.4: memory.db (읽기 전용)
- v3.0.0: memory_v3.db (읽기/쓰기)
- 장점: 깨끗한 분리, 롤백 쉬움
- 단점: 저장 공간 2배

옵션 B: 통합 관리
- 단일 DB에 v2/v3 테이블 공존
- 장점: 공간 효율적
- 단점: 복잡도 증가, 롤백 어려움
```

### 2. **AI 모델 선택**
```
옵션 A: Claude (via MCP)
- 장점: 통합 쉬움, 컨텍스트 공유
- 단점: MCP 의존성

옵션 B: 전용 파싱 모델
- 장점: 최적화 가능, 빠른 속도
- 단점: 별도 관리 필요
```

### 3. **마이그레이션 시점**
```
옵션 A: Lazy Loading
- 접근시마다 필요한 것만 파싱
- 장점: 초기 부담 없음
- 단점: 첫 접근 지연

옵션 B: Batch Migration
- 모든 데이터 일괄 변환
- 장점: 일관성, 예측 가능
- 단점: 초기 시간/비용
```

---

## 💡 **추천 구현 방향**

1. **v3.0.0 전용 DB 생성** (memory_v3.db)
2. **Lazy + Batch 혼합**: 중요 메모리는 미리, 나머지는 필요시
3. **3단계 폴백**: AI → 로컬파서 → Raw저장
4. **캐싱 필수**: 한 번 파싱한 결과는 보존
5. **Human-in-the-loop**: 낮은 신뢰도는 사용자 확인

이 방식이면:
- ✅ 기존 데이터 완벽 보존
- ✅ 점진적 품질 개선
- ✅ AI 장애시도 작동
- ✅ 비용 통제 가능
- ✅ 언제든 롤백 가능
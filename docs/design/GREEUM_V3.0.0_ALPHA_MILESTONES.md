# Greeum v3.0.0 Alpha Milestones
## 구조화된 지능형 메모리 시스템 구축

**Alpha Phase Duration**: 3-4개월 (2025.01 ~ 2025.04)  
**Base Version**: v2.6.4.post1 (Stable Production)

---

## 🎯 **Alpha 전체 목표**

**"비구조화 텍스트 → 구조화된 지식 체계 전환"**

### 핵심 성과 지표
- 📊 액탄트 파싱 정확도: 0% → 80%
- 🔗 인과관계 추론 정확도: 20% → 70%
- 🎯 동일성 매칭 정확도: 0% → 60%
- ⚡ 성능 유지: <50ms 응답 시간

---

## 📅 **Alpha 1: 액탄트 파싱 엔진** (4-6주)

### 🎯 목표
**모든 메모리를 [주체-행동-객체] 구조로 변환**

### 📋 작업 항목

#### Week 1-2: 기존 파서 활성화 및 분석
```python
# 주요 작업
1. v2.5.3 AIActantParser 코드 리뷰 및 테스트
2. 기존 247개 메모리 샘플 분석
3. 파싱 패턴 카테고리화
4. 한국어/영어 파싱 규칙 정의

# 성공 기준
✓ 파서 모듈 100% 이해
✓ 테스트 데이터셋 50개 준비
✓ 파싱 규칙 문서화
```

#### Week 3-4: 파싱 엔진 구현
```python
class EnhancedActantParser:
    """v3.0.0 강화된 액탄트 파서"""
    
    def parse_memory(self, text: str) -> ActantStructure:
        # 1. 언어 감지 (한/영/혼합)
        language = self.detect_language(text)
        
        # 2. 패턴 기반 파싱
        if self.has_explicit_pattern(text):
            return self.pattern_based_parsing(text)
        
        # 3. NLP 기반 파싱 (형태소 분석)
        tokens = self.tokenize(text, language)
        subject = self.extract_subject(tokens)
        action = self.extract_action(tokens)
        object = self.extract_object(tokens)
        
        # 4. 신뢰도 계산
        confidence = self.calculate_confidence(subject, action, object)
        
        return ActantStructure(subject, action, object, confidence)

# 구현 목표
✓ 명시적 패턴 90% 정확도
✓ 암묵적 패턴 70% 정확도  
✓ 다국어 지원 (한/영)
```

#### Week 5-6: 기존 메모리 마이그레이션
```sql
-- 마이그레이션 프로세스
1. 백업 생성 (data/backup_v264/)
2. 배치 파싱 (50개씩)
3. 검증 및 수정
4. 신뢰도 기반 필터링
5. 최종 커밋

-- 예상 결과
UPDATE blocks SET 
    actant_subject = 'Claude',
    actant_action = '구현',
    actant_object = 'v2.7.0 Phase 1',
    actant_parsed_at = '2025-01-15T10:00:00',
    migration_confidence = 0.85
WHERE block_index = 223;
```

### 📊 Alpha 1 성공 지표
| 지표 | 목표 | 측정 방법 |
|------|------|-----------|
| 파싱 정확도 | 80% | 수동 검증 100개 샘플 |
| 파싱 속도 | <30ms | 평균 응답 시간 |
| 마이그레이션 | 100% | 247개 블록 완료 |
| 신뢰도 분포 | 70% > 0.7 | confidence 분포 |

### 🧪 테스트 시나리오
```python
test_cases = [
    # 명시적 패턴
    ("[사용자-요청-기능개선]", ("사용자", "요청", "기능개선"), 0.95),
    ("Claude가 버그를 수정했다", ("Claude", "수정", "버그"), 0.90),
    
    # 암묵적 패턴  
    ("프로젝트가 성공했다", ("프로젝트", "성공", None), 0.70),
    ("코딩을 많이 했다", (None, "코딩", None), 0.60),
    
    # 복잡한 패턴
    ("팀이 프로젝트를 완성해서 보너스를 받았다", 
     ("팀", "완성", "프로젝트"), 0.75)
]
```

---

## 📅 **Alpha 2: 동일성 해시 시스템** (4-6주)

### 🎯 목표
**동일한 주체/행동/객체를 정확하게 식별**

### 📋 작업 항목

#### Week 1-2: 핵심 해시맵 구축
```python
class ActantHashMapper:
    """액탄트 동일성 매핑 시스템"""
    
    def __init__(self):
        # 수동 정의 핵심 매핑 (100개)
        self.core_mappings = {
            "subjects": {
                "user": ["사용자", "유저", "user", "나", "내가", "제가"],
                "claude": ["Claude", "claude", "AI", "assistant", "어시스턴트"],
                "team": ["팀", "team", "개발팀", "우리", "우리팀"],
                "system": ["시스템", "system", "서버", "프로그램", "앱"]
            },
            "actions": {
                "request": ["요청", "부탁", "ask", "request", "요구"],
                "implement": ["구현", "개발", "만들기", "implement", "develop"],
                "complete": ["완료", "완성", "끝", "finish", "done"],
                "fix": ["수정", "고치기", "fix", "패치", "debug"]
            },
            "objects": {
                "project": ["프로젝트", "project", "작업", "태스크"],
                "feature": ["기능", "feature", "함수", "API"],
                "bug": ["버그", "bug", "오류", "에러", "문제"]
            }
        }

# 구현 목표
✓ 100개 핵심 액탄트 정의
✓ 다국어 변형 포함
✓ 유사어 그룹화
```

#### Week 3-4: 패턴 매칭 및 정규화
```python
def normalize_actant(self, text: str, actant_type: str) -> str:
    """액탄트 텍스트를 정규화된 해시로 변환"""
    
    # 1. 정확 매칭 (신뢰도 0.9)
    if exact_match := self.exact_match(text, actant_type):
        return exact_match
    
    # 2. 패턴 매칭 (신뢰도 0.7)
    if pattern_match := self.pattern_match(text, actant_type):
        return pattern_match
    
    # 3. 유사도 매칭 (신뢰도 0.5)
    if similarity_match := self.similarity_match(text, actant_type):
        return similarity_match
    
    # 4. 새로운 해시 생성
    return self.generate_new_hash(text, actant_type)

# 테스트 케이스
assert normalize_actant("사용자", "subject") == "subject_user"
assert normalize_actant("유저", "subject") == "subject_user"
assert normalize_actant("내가", "subject") == "subject_user"
```

#### Week 5-6: 학습 시스템 구현
```python
class AdaptiveHashLearner:
    """사용자 피드백 기반 해시 학습"""
    
    def learn_from_feedback(self, actant1, actant2, is_same: bool):
        # 피드백 저장
        self.feedback_store.add({
            "actant1": actant1,
            "actant2": actant2,
            "is_same": is_same,
            "timestamp": datetime.now()
        })
        
        # 패턴 학습
        if is_same and self.confidence_threshold_met():
            self.merge_actants(actant1, actant2)
        
    def suggest_merges(self) -> List[MergeSuggestion]:
        # 자주 함께 나타나는 액탄트 제안
        return self.analyze_co_occurrence()
```

### 📊 Alpha 2 성공 지표
| 지표 | 목표 | 측정 방법 |
|------|------|-----------|
| 매칭 정확도 | 60% | 테스트셋 검증 |
| False Positive | <30% | 오매칭 비율 |
| 학습 효과 | 10% 개선 | 피드백 후 정확도 |
| 처리 속도 | <10ms | 해시 변환 시간 |

---

## 📅 **Alpha 3: 구조 기반 인과관계** (4-6주)

### 🎯 목표
**액탄트 구조를 활용한 진정한 인과관계 추론**

### 📋 작업 항목

#### Week 1-2: 구조적 관계 정의
```python
class StructuralCausalReasoner:
    """액탄트 구조 기반 인과관계 추론"""
    
    def analyze_causal_relationship(self, block1, block2):
        # 1. 액탄트 동일성 체크
        subject_match = self.compare_subjects(block1, block2)
        object_match = self.compare_objects(block1, block2)
        
        # 2. 행동 인과성 분석
        action_causality = self.analyze_action_sequence(
            block1.actant_action, 
            block2.actant_action
        )
        
        # 3. 시간적 검증
        temporal_validity = self.validate_temporal_order(
            block1.timestamp, 
            block2.timestamp
        )
        
        # 4. 종합 신뢰도
        confidence = self.calculate_structural_confidence(
            subject_match, object_match, 
            action_causality, temporal_validity
        )
        
        return CausalRelation(block1, block2, confidence)

# 인과관계 규칙 예시
CAUSAL_ACTION_RULES = {
    ("요청", "구현"): 0.8,  # 요청 → 구현
    ("구현", "완료"): 0.9,  # 구현 → 완료
    ("완료", "배포"): 0.85, # 완료 → 배포
    ("오류", "수정"): 0.9,  # 오류 → 수정
}
```

#### Week 3-4: 관계 추론 엔진
```python
def infer_causal_chains(self, memories: List[Memory]) -> CausalGraph:
    """메모리 집합에서 인과관계 그래프 구축"""
    
    graph = CausalGraph()
    
    # 1. 모든 쌍 비교 (최적화 필요)
    for i, mem1 in enumerate(memories):
        for mem2 in memories[i+1:]:
            if relation := self.analyze_causal_relationship(mem1, mem2):
                if relation.confidence > 0.6:
                    graph.add_edge(mem1, mem2, relation)
    
    # 2. 전이적 관계 추론
    graph.infer_transitive_relations()
    
    # 3. 모순 제거
    graph.resolve_contradictions()
    
    return graph
```

#### Week 5-6: 성능 최적화 및 검증
```python
# 최적화 전략
1. 인덱싱: 액탄트 해시 기반 빠른 검색
2. 캐싱: 자주 접근하는 관계 캐시
3. 배치 처리: 50개씩 묶어서 처리
4. 병렬화: 멀티스레드 비교 연산

# 검증 메트릭
- 정확도: 수동 라벨링 100개와 비교
- 재현율: 실제 관계 중 찾은 비율
- 정밀도: 찾은 관계 중 정확한 비율
- F1 스코어: 종합 성능 지표
```

### 📊 Alpha 3 성공 지표
| 지표 | 목표 | 측정 방법 |
|------|------|-----------|
| 인과관계 정확도 | 70% | F1 스코어 |
| 시간순서 위반 | 0% | 역방향 관계 수 |
| False Positive | <20% | 허위 관계 비율 |
| 처리 성능 | <100ms | 50개 블록 처리 |

---

## 🧪 **Alpha 통합 테스트 계획**

### 종단간 시나리오
```python
# 시나리오: 프로젝트 개발 스토리
memories = [
    "사용자가 새 기능을 요청했다",           # Block 1
    "Claude가 기능 설계를 시작했다",         # Block 2  
    "개발팀이 프로토타입을 구현했다",        # Block 3
    "테스트에서 버그가 발견되었다",          # Block 4
    "개발자가 버그를 수정했다",              # Block 5
    "최종 테스트를 통과했다",                # Block 6
    "사용자가 기능에 만족했다"               # Block 7
]

# 예상 결과
expected_actants = [
    ("사용자", "요청", "새 기능"),
    ("Claude", "시작", "기능 설계"),
    ("개발팀", "구현", "프로토타입"),
    ("테스트", "발견", "버그"),
    ("개발자", "수정", "버그"),
    (None, "통과", "최종 테스트"),
    ("사용자", "만족", "기능")
]

expected_causality = [
    (1, 2, 0.85),  # 요청 → 설계 시작
    (2, 3, 0.80),  # 설계 → 구현
    (3, 4, 0.75),  # 구현 → 버그 발견
    (4, 5, 0.90),  # 버그 발견 → 수정
    (5, 6, 0.85),  # 수정 → 테스트 통과
    (6, 7, 0.80)   # 통과 → 만족
]
```

### 성능 벤치마크
```python
# 대규모 데이터 테스트
- 1,000개 메모리: <1초
- 10,000개 메모리: <10초
- 100,000개 메모리: <2분

# 메모리 사용량
- 기본: <256MB
- 1,000개: <512MB
- 10,000개: <1GB
```

---

## 🚀 **Alpha 개발 환경 설정**

### 브랜치 전략
```bash
main (v2.6.4.post1)
├── develop-v3
│   ├── alpha-1-actant-parser
│   ├── alpha-2-hash-system
│   └── alpha-3-causal-reasoning
└── hotfix-v2.6.5
```

### 개발 도구
```python
# 필수 패키지
dependencies = {
    "core": ["sqlite3", "numpy", "click"],
    "nlp": ["konlpy", "nltk", "spacy"],
    "ml": ["scikit-learn", "sentence-transformers"],
    "test": ["pytest", "pytest-cov", "pytest-benchmark"]
}

# 개발 환경
- Python 3.10+
- SQLite 3.35+
- 가상환경 권장
```

### CI/CD 파이프라인
```yaml
# .github/workflows/alpha-test.yml
on:
  push:
    branches: [develop-v3, alpha-*]

jobs:
  test:
    - lint (ruff, black)
    - unit-tests (pytest)
    - integration-tests
    - performance-benchmark
    - coverage-report (>80%)
```

---

## 📋 **Alpha 완료 기준**

### 필수 달성 항목
- [x] 액탄트 파싱 80% 정확도
- [x] 동일성 매칭 60% 정확도
- [x] 인과관계 추론 70% 정확도
- [x] 성능 <100ms 유지
- [x] 기존 데이터 100% 마이그레이션

### 문서화
- [x] API 문서 완성
- [x] 개발자 가이드
- [x] 사용자 매뉴얼
- [x] 마이그레이션 가이드

### 품질 보증
- [x] 단위 테스트 커버리지 80%
- [x] 통합 테스트 통과
- [x] 성능 벤치마크 달성
- [x] 보안 검토 완료

---

## 🎯 **다음 단계: Beta 준비**

Alpha 완료 후 Beta에서 추가될 기능:
- 🧠 의미적 임베딩 (BERT/RoBERTa)
- ⏰ 시계열 패턴 분석
- 💡 능동적 인사이트 생성
- 📊 시각화 대시보드

**Alpha 성공 = v3.0.0의 견고한 기반 완성!**
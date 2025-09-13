# 액탄트 동일성 해시 시스템: 현실적 구현 설계

## 🎯 설계 원칙
**"완벽한 정확도보다 실용적인 개선"** - 20% → 60-70% 목표

## 📊 계층적 매칭 시스템

### Level 1: 완전 일치 (높은 신뢰도)
```python
exact_match = {
    "subjects": {
        "user_hash_001": ["사용자", "유저", "user"],
        "claude_hash_002": ["Claude", "claude", "AI", "어시스턴트"],
        "team_hash_003": ["팀", "team", "개발팀"]
    },
    "actions": {
        "request_hash_001": ["요청", "request", "부탁"],
        "implement_hash_002": ["구현", "개발", "implement", "develop"],
        "complete_hash_003": ["완료", "완성", "complete", "finish"]
    },
    "objects": {
        "project_hash_001": ["프로젝트", "project", "작업"],
        "prototype_hash_002": ["프로토타입", "prototype", "시제품"]
    }
}
```

### Level 2: 패턴 매칭 (중간 신뢰도)
```python
pattern_rules = {
    "subject_patterns": [
        r"^(사용자|유저|user).*$",  # 사용자 관련
        r"^(개발자|dev|developer).*$",  # 개발자 관련
        r"^(팀|team).*$"  # 팀 관련
    ],
    "action_patterns": [
        r".*요청.*|.*request.*",  # 요청 행동
        r".*구현.*|.*개발.*|.*implement.*|.*develop.*",  # 개발 행동
        r".*완료.*|.*완성.*|.*complete.*|.*finish.*"  # 완료 행동
    ]
}
```

### Level 3: 의미적 유사도 (낮은 신뢰도)
```python
# 간단한 임베딩 유사도 (코사인 유사도 > 0.7)
semantic_threshold = 0.7
```

## 🔧 실용적 구현 전략

### 1단계: 수동 정의 해시맵 (즉시 적용 가능)
```python
class ActantHashManager:
    def __init__(self):
        # 수동으로 정의된 핵심 액탄트들
        self.subject_hashes = {
            "user": ["사용자", "유저", "나", "내가", "user"],
            "claude": ["Claude", "claude", "AI", "어시스턴트", "assistant"],
            "team": ["팀", "team", "개발팀", "우리팀"],
            "system": ["시스템", "system", "서버", "프로그램"]
        }
        
        self.action_hashes = {
            "request": ["요청", "부탁", "request", "ask"],
            "implement": ["구현", "개발", "만들기", "코딩", "implement", "develop", "code"],
            "complete": ["완료", "완성", "끝", "complete", "finish", "done"],
            "test": ["테스트", "확인", "검증", "test", "verify", "check"],
            "fix": ["수정", "고치기", "fix", "repair", "debug"]
        }
        
        self.object_hashes = {
            "project": ["프로젝트", "project", "작업", "일"],
            "feature": ["기능", "feature", "함수", "function"],
            "bug": ["버그", "bug", "오류", "error", "문제"],
            "code": ["코드", "code", "소스", "프로그램"],
            "api": ["API", "api", "인터페이스", "interface"]
        }
    
    def get_subject_hash(self, subject_text: str) -> str:
        for hash_key, variants in self.subject_hashes.items():
            if any(variant.lower() in subject_text.lower() for variant in variants):
                return f"subject_{hash_key}"
        return f"subject_unknown_{hash(subject_text)}"
    
    def get_action_hash(self, action_text: str) -> str:
        for hash_key, variants in self.action_hashes.items():
            if any(variant.lower() in action_text.lower() for variant in variants):
                return f"action_{hash_key}"
        return f"action_unknown_{hash(action_text)}"
    
    def get_object_hash(self, object_text: str) -> str:
        for hash_key, variants in self.object_hashes.items():
            if any(variant.lower() in object_text.lower() for variant in variants):
                return f"object_{hash_key}"
        return f"object_unknown_{hash(object_text)}"
```

### 2단계: 패턴 기반 정규화 (중기)
```python
def normalize_actant(text: str, actant_type: str) -> str:
    """액탄트 텍스트를 정규화된 해시로 변환"""
    
    # 1단계: 기본 전처리
    text = text.lower().strip()
    text = re.sub(r'[^\w\s가-힣]', '', text)  # 특수문자 제거
    
    # 2단계: 패턴 매칭
    if actant_type == "subject":
        if any(word in text for word in ["사용자", "유저", "user", "나", "내가"]):
            return "subject_user"
        elif any(word in text for word in ["claude", "ai", "어시스턴트"]):
            return "subject_claude"
        elif any(word in text for word in ["팀", "team", "개발팀"]):
            return "subject_team"
    
    # 3단계: 기본 해시 (매칭 실패시)
    return f"{actant_type}_{hashlib.md5(text.encode()).hexdigest()[:8]}"
```

### 3단계: 학습 기반 개선 (장기)
```python
class AdaptiveActantMatcher:
    def __init__(self):
        self.feedback_data = []  # 사용자 피드백 저장
        
    def add_feedback(self, actant1: str, actant2: str, is_same: bool):
        """사용자 피드백으로 매칭 정확도 개선"""
        self.feedback_data.append({
            "actant1": actant1,
            "actant2": actant2, 
            "is_same": is_same,
            "timestamp": datetime.now()
        })
        
    def learn_patterns(self):
        """피드백 데이터로 매칭 패턴 학습"""
        # 간단한 규칙 학습 로직
        pass
```

## 📊 예상 성능 개선

| 접근법 | 정확도 | 구현 복잡도 | 적용 시기 |
|--------|--------|-------------|-----------|
| 현재 키워드 매칭 | 20% | 낮음 | ✅ 완료 |
| 수동 해시맵 | 50-60% | 중간 | 🎯 1주 |
| 패턴 정규화 | 60-70% | 높음 | 📅 2-3주 |
| 의미적 매칭 | 70-80% | 매우 높음 | 📅 4-6주 |

## 🚀 현실적 시작점

**즉시 적용 가능한 최소 실행 가능 제품(MVP):**

1. **20개 핵심 액탄트 해시맵** 수동 정의
2. **단순 문자열 포함 매칭**으로 시작  
3. **점진적 피드백 수집**으로 개선
4. **80% 정확도 달성시 의미적 분석 추가**

이 방식이면 **현재 20% → 50-60%로 2-3배 개선**은 확실하고, 장기적으로 80% 근접도 가능할 것입니다.

## 🎯 결론

**완벽하지 않지만 실용적인** 시스템으로 시작해서, 사용하면서 점진적으로 개선하는 방향이 가장 현실적입니다. 

핵심은 **"이론적 완벽함보다 실제 사용 가능한 개선"**입니다.
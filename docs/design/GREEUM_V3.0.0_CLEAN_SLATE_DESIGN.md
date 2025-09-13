# Greeum v3.0.0: Clean Slate Design
## AI-Native Memory System (호환성 제로)

---

## 🎯 **핵심 철학**

**"AI가 직접 이해하고 저장하는 메모리 시스템"**

- ❌ v2.x와의 호환성 고려 안함
- ❌ 외부 API 사용 안함  
- ✅ MCP로 연결된 AI가 모든 처리
- ✅ AI가 직접 구조화해서 저장

---

## 📐 **v3.0.0 아키텍처**

### 1. **AI가 직접 채우는 스키마**

```python
@dataclass
class V3Memory:
    """AI가 직접 작성하는 메모리 구조"""
    
    # Core Identity
    memory_id: str
    timestamp: datetime
    
    # Actant Structure (AI가 직접 파싱)
    subject: str          # 누가
    action: str           # 무엇을
    object: str           # 누구에게/무엇에
    
    # Extended Actants (AI가 추론)
    sender: Optional[str]     # 요청자
    receiver: Optional[str]   # 수혜자
    context: Optional[str]    # 상황/배경
    
    # AI Analysis
    intent: str              # AI가 파악한 의도
    emotion: str             # AI가 감지한 감정
    importance: float        # AI가 판단한 중요도
    
    # Relations (AI가 발견)
    causes: List[str]        # 원인이 되는 메모리들
    effects: List[str]       # 결과가 되는 메모리들
    related: List[str]       # 연관된 메모리들
    
    # Raw
    original_text: str       # 원본 보존
```

### 2. **MCP 도구 정의**

```python
# greeum/mcp/v3_tools.py

class V3MemoryTools:
    """v3.0.0 전용 MCP 도구"""
    
    @tool(name="v3_add_memory")
    async def add_structured_memory(
        self,
        text: str,
        context: Optional[str] = None
    ) -> Dict:
        """
        AI가 텍스트를 분석해서 구조화된 메모리 생성
        
        AI가 수행할 작업:
        1. 액탄트 구조 파싱
        2. 의도와 감정 분석
        3. 중요도 판단
        4. 기존 메모리와의 관계 파악
        """
        
        # AI가 직접 채움 (MCP 환경에서)
        memory = {
            "subject": "AI가 파싱한 주체",
            "action": "AI가 파싱한 행동",
            "object": "AI가 파싱한 객체",
            "intent": "AI가 분석한 의도",
            "emotion": "AI가 감지한 감정",
            "importance": 0.0,  # AI가 판단
            "causes": [],       # AI가 찾은 원인들
            "effects": [],      # AI가 예측한 결과들
            "original_text": text
        }
        
        return self.save_v3_memory(memory)
    
    @tool(name="v3_search_semantic")
    async def search_by_meaning(
        self,
        query: str,
        limit: int = 10
    ) -> List[Dict]:
        """
        AI가 의미 기반으로 검색
        단순 키워드가 아닌 의도 파악
        """
        # AI가 쿼리 의도 파악
        intent = "AI가 파악한 검색 의도"
        
        # 의미적으로 관련된 메모리 찾기
        results = self.semantic_search(intent)
        
        return results
    
    @tool(name="v3_analyze_patterns")
    async def find_patterns(
        self,
        time_range: Optional[str] = None
    ) -> Dict:
        """
        AI가 메모리 패턴 분석
        """
        patterns = {
            "recurring_subjects": [],  # 반복되는 주체
            "common_actions": [],       # 자주 하는 행동
            "causal_chains": [],        # 인과 관계 체인
            "emotional_trends": []      # 감정 변화 추이
        }
        
        return patterns
```

### 3. **실제 사용 흐름**

```python
# Claude/AI가 직접 실행하는 코드

# 1. 새 메모리 추가시
user_text = "버그 수정 완료했고 배포 준비 중"

# AI가 직접 분석해서 저장
memory = await mcp.v3_add_memory(
    text=user_text,
    context="프로젝트 마무리 단계"
)

# AI가 채운 구조:
{
    "subject": "개발자",      # AI가 추론
    "action": "수정",
    "object": "버그",
    "intent": "작업 완료 보고",
    "emotion": "성취감",
    "importance": 0.75,
    "causes": ["memory_245"],  # 이전 버그 리포트
    "effects": ["memory_262"], # 배포 관련
    "original_text": "버그 수정 완료했고 배포 준비 중"
}

# 2. 검색시
results = await mcp.v3_search_semantic(
    query="최근에 해결한 문제들"
)
# AI가 "해결한 문제"의 의미를 이해하고 관련 메모리 반환

# 3. 패턴 분석
patterns = await mcp.v3_analyze_patterns(
    time_range="last_week"
)
# AI가 일주일간의 행동 패턴 분석
```

---

## 🗄️ **단순화된 DB 스키마**

```sql
-- v3.0.0 전용 테이블 (v2.x와 완전 분리)
CREATE TABLE v3_memories (
    memory_id TEXT PRIMARY KEY,
    timestamp TEXT NOT NULL,
    
    -- Actants
    subject TEXT,
    action TEXT,
    object TEXT,
    sender TEXT,
    receiver TEXT,
    context TEXT,
    
    -- AI Analysis
    intent TEXT,
    emotion TEXT,
    importance REAL,
    
    -- Relations (JSON arrays)
    causes TEXT,      -- ["mem_1", "mem_2"]
    effects TEXT,     -- ["mem_3"]
    related TEXT,     -- ["mem_4", "mem_5"]
    
    -- Original
    original_text TEXT NOT NULL,
    
    -- Metadata
    ai_model TEXT,    -- 어떤 AI가 처리했는지
    confidence REAL,
    created_at TEXT
);

-- 심플한 인덱스
CREATE INDEX idx_v3_timestamp ON v3_memories(timestamp);
CREATE INDEX idx_v3_subject ON v3_memories(subject);
CREATE INDEX idx_v3_action ON v3_memories(action);
CREATE INDEX idx_v3_importance ON v3_memories(importance);
```

---

## 💡 **장점**

1. **단순함**: 복잡한 마이그레이션 불필요
2. **정확도**: AI가 직접 이해하고 저장
3. **유연성**: AI 모델 개선시 자동 향상
4. **독립성**: v2.x 코드와 완전 분리
5. **자연스러움**: AI와 사용자가 같은 방식으로 이해

---

## 🚀 **구현 단계**

### Week 1: 기초
```python
# 1. 새 DB 파일 생성
v3_db = "data/greeum_v3.db"

# 2. 테이블 생성
create_v3_tables()

# 3. MCP 도구 등록
register_v3_tools()
```

### Week 2: AI 통합
```python
# Claude/GPT가 직접 사용할 도구들
- v3_add_memory()      # 구조화 저장
- v3_search_semantic() # 의미 검색
- v3_find_relations()  # 관계 발견
- v3_analyze_patterns() # 패턴 분석
```

### Week 3: 실사용
```python
# 모든 새 메모리는 v3로
# v2.x는 읽기 전용으로 남김
# 필요하면 AI가 v2 메모리 읽어서 v3로 재저장
```

---

## 🎯 **핵심 차이점**

### v2.x (기존)
- 텍스트 → 파서 → 구조 → 저장
- 파서 정확도에 의존
- 규칙 기반 처리

### v3.0 (새로운)
- 텍스트 → AI 이해 → 직접 구조화 → 저장
- AI 이해력에 의존
- 의미 기반 처리

---

## 📝 **결론**

**"파서를 만들지 말고, AI가 직접 이해하게 하자"**

- 호환성 버림 → 깨끗한 설계
- API 안씀 → MCP로 로컬 AI 활용
- 마이그레이션 최소화 → 필요시만 AI가 변환
- 복잡도 제거 → AI가 알아서 처리

이게 진정한 **AI-Native Memory System**입니다.
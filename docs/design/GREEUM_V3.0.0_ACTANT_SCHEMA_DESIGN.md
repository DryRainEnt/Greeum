# Greeum v3.0.0: 액탄트 모델 기반 메모리 스키마 설계
## Greimas 6-Actant Model 적용

---

## 📐 **액탄트 모델 개요**

### Greimas의 6개 액탄트 역할
1. **Subject (주체)**: 행동을 수행하는 주인공
2. **Object (객체)**: 주체가 추구하는 목표/대상
3. **Sender (발신자)**: 주체에게 임무를 부여하는 존재
4. **Receiver (수신자)**: 행동의 결과를 받는 존재
5. **Helper (조력자)**: 주체를 돕는 존재
6. **Opponent (대립자)**: 주체를 방해하는 존재

### 단순화된 3-요소 구조 (Primary)
- **Subject (주체)**: WHO - 누가
- **Action (행동)**: WHAT - 무엇을
- **Object (객체)**: WHOM/WHAT - 누구에게/무엇에

---

## 🗄️ **데이터베이스 스키마 확장**

### 1. 액탄트 구조 테이블

```sql
-- 액탄트 구조화된 메모리 (v3.0.0)
CREATE TABLE IF NOT EXISTS memory_actants (
    actant_id TEXT PRIMARY KEY,
    memory_id INTEGER,
    
    -- Primary Actants (필수)
    subject_raw TEXT,           -- 원본 주체 텍스트
    subject_hash TEXT,          -- 정규화된 주체 해시
    action_raw TEXT,            -- 원본 행동 텍스트  
    action_hash TEXT,           -- 정규화된 행동 해시
    object_raw TEXT,            -- 원본 객체 텍스트
    object_hash TEXT,           -- 정규화된 객체 해시
    
    -- Secondary Actants (선택)
    sender_raw TEXT,            -- 발신자 (요청자)
    sender_hash TEXT,
    receiver_raw TEXT,          -- 수신자 (수혜자)
    receiver_hash TEXT,
    helper_raw TEXT,            -- 조력자
    helper_hash TEXT,
    opponent_raw TEXT,          -- 대립자 (문제/장애물)
    opponent_hash TEXT,
    
    -- Metadata
    confidence REAL DEFAULT 0.5, -- 파싱 신뢰도
    parser_version TEXT,         -- 파서 버전
    parsed_at TEXT,             -- 파싱 시간
    metadata TEXT,              -- 추가 메타데이터
    
    FOREIGN KEY (memory_id) REFERENCES blocks(block_index)
);

-- 엔티티 정규화 테이블
CREATE TABLE IF NOT EXISTS actant_entities (
    entity_hash TEXT PRIMARY KEY,
    entity_type TEXT,           -- 'subject', 'object', 'person', 'system', etc.
    canonical_form TEXT,        -- 정규화된 표준 형태
    variations TEXT,            -- JSON array of variations ["사용자", "user", "유저"]
    first_seen TEXT,            -- 최초 발견 시간
    last_seen TEXT,             -- 최근 발견 시간
    occurrence_count INTEGER DEFAULT 1,
    metadata TEXT
);

-- 행동 정규화 테이블  
CREATE TABLE IF NOT EXISTS actant_actions (
    action_hash TEXT PRIMARY KEY,
    action_type TEXT,           -- 'request', 'create', 'modify', 'complete', etc.
    canonical_form TEXT,        -- 정규화된 표준 형태
    variations TEXT,            -- JSON array ["요청", "request", "요구"]
    tense TEXT,                 -- 'past', 'present', 'future'
    aspect TEXT,                -- 'completed', 'ongoing', 'planned'
    first_seen TEXT,
    last_seen TEXT,
    occurrence_count INTEGER DEFAULT 1,
    metadata TEXT
);

-- 액탄트 관계 테이블
CREATE TABLE IF NOT EXISTS actant_relations (
    relation_id TEXT PRIMARY KEY,
    source_actant_id TEXT,
    target_actant_id TEXT,
    relation_type TEXT,         -- 'causal', 'temporal', 'conditional', 'opposition'
    strength REAL DEFAULT 0.5,
    evidence_count INTEGER DEFAULT 1,
    created_at TEXT,
    last_updated TEXT,
    metadata TEXT,
    
    FOREIGN KEY (source_actant_id) REFERENCES memory_actants(actant_id),
    FOREIGN KEY (target_actant_id) REFERENCES memory_actants(actant_id)
);

-- 인덱스 생성
CREATE INDEX IF NOT EXISTS idx_actants_memory ON memory_actants(memory_id);
CREATE INDEX IF NOT EXISTS idx_actants_subject ON memory_actants(subject_hash);
CREATE INDEX IF NOT EXISTS idx_actants_action ON memory_actants(action_hash);
CREATE INDEX IF NOT EXISTS idx_actants_object ON memory_actants(object_hash);
CREATE INDEX IF NOT EXISTS idx_entities_type ON actant_entities(entity_type);
CREATE INDEX IF NOT EXISTS idx_actions_type ON actant_actions(action_type);
CREATE INDEX IF NOT EXISTS idx_relations_source ON actant_relations(source_actant_id);
CREATE INDEX IF NOT EXISTS idx_relations_target ON actant_relations(target_actant_id);
```

---

## 🔄 **액탄트 파싱 플로우**

### 1. 메모리 입력 처리

```python
# 입력 예시
memory_text = "사용자가 버그 수정을 요청했고 Claude가 해결했다"

# 파싱 결과
actants = {
    # 첫 번째 액탄트 구조
    "actant_1": {
        "subject": "사용자",
        "action": "요청",
        "object": "버그 수정",
        "sender": None,  # 암묵적: 사용자 자신
        "receiver": "Claude",  # 암묵적 추론
    },
    
    # 두 번째 액탄트 구조  
    "actant_2": {
        "subject": "Claude",
        "action": "해결",
        "object": "버그",
        "sender": "사용자",  # 요청자
        "receiver": "사용자",  # 수혜자
    }
}
```

### 2. 엔티티 정규화

```python
# 동일 엔티티 매핑
entity_mappings = {
    "user_001": ["사용자", "유저", "user", "고객", "클라이언트"],
    "claude_001": ["Claude", "claude", "AI", "assistant", "어시스턴트"],
    "bug_001": ["버그", "bug", "오류", "에러", "error", "문제"]
}

# 해시 생성
def get_entity_hash(entity_text, entity_type):
    # 1. 기존 매핑 확인
    for hash_id, variations in entity_mappings.items():
        if entity_text.lower() in [v.lower() for v in variations]:
            return hash_id
    
    # 2. 새 엔티티 생성
    return create_new_entity_hash(entity_text, entity_type)
```

### 3. 행동 정규화

```python
# 행동 분류 체계
action_taxonomy = {
    "request": {
        "canonical": "요청",
        "variations": ["요청", "부탁", "요구", "신청", "request", "ask"],
        "type": "communication"
    },
    "solve": {
        "canonical": "해결",
        "variations": ["해결", "수정", "고침", "fix", "solve", "resolve"],
        "type": "modification"
    },
    "create": {
        "canonical": "생성",
        "variations": ["생성", "만들기", "작성", "create", "make", "write"],
        "type": "creation"
    }
}
```

---

## 🔗 **Association Network 연동**

### 1. 액탄트 → 노드 변환

```python
class ActantToNodeBridge:
    """액탄트 구조를 Association Network 노드로 변환"""
    
    def convert_actant_to_nodes(self, actant: Dict) -> List[MemoryNode]:
        nodes = []
        
        # Subject 노드
        if actant.get('subject_hash'):
            subject_node = MemoryNode(
                node_id=f"entity_{actant['subject_hash']}",
                node_type='entity',
                content=actant['subject_raw']
            )
            nodes.append(subject_node)
        
        # Action 노드
        if actant.get('action_hash'):
            action_node = MemoryNode(
                node_id=f"action_{actant['action_hash']}",
                node_type='action',
                content=actant['action_raw']
            )
            nodes.append(action_node)
        
        # Object 노드
        if actant.get('object_hash'):
            object_node = MemoryNode(
                node_id=f"entity_{actant['object_hash']}",
                node_type='entity',
                content=actant['object_raw']
            )
            nodes.append(object_node)
        
        return nodes
    
    def create_actant_associations(self, actant: Dict) -> List[Association]:
        associations = []
        
        # Subject → Action
        if actant.get('subject_hash') and actant.get('action_hash'):
            associations.append(Association(
                source_node_id=f"entity_{actant['subject_hash']}",
                target_node_id=f"action_{actant['action_hash']}",
                association_type='performs',
                strength=0.9
            ))
        
        # Action → Object
        if actant.get('action_hash') and actant.get('object_hash'):
            associations.append(Association(
                source_node_id=f"action_{actant['action_hash']}",
                target_node_id=f"entity_{actant['object_hash']}",
                association_type='targets',
                strength=0.9
            ))
        
        return associations
```

### 2. 인과관계 추론

```python
class ActantCausalReasoner:
    """액탄트 기반 인과관계 추론"""
    
    def find_causal_chains(self, actants: List[Dict]) -> List[CausalChain]:
        chains = []
        
        for i, actant1 in enumerate(actants):
            for actant2 in actants[i+1:]:
                # Object-Subject 매칭
                if actant1['object_hash'] == actant2['subject_hash']:
                    # A의 결과가 B의 주체가 됨
                    chains.append(CausalChain(
                        cause=actant1,
                        effect=actant2,
                        type='object_becomes_subject',
                        confidence=0.8
                    ))
                
                # Same Subject Sequential Actions
                if actant1['subject_hash'] == actant2['subject_hash']:
                    # 같은 주체의 연속 행동
                    chains.append(CausalChain(
                        cause=actant1,
                        effect=actant2,
                        type='sequential_action',
                        confidence=0.6
                    ))
        
        return chains
```

---

## 📊 **예상 데이터 구조**

### 실제 메모리 예시

```json
{
  "memory_id": 247,
  "context": "프로젝트 마일스톤 달성해서 팀이 축하했다",
  "actants": {
    "actant_id": "act_001",
    "subject_raw": "팀",
    "subject_hash": "team_001",
    "action_raw": "축하했다",
    "action_hash": "celebrate_001",
    "object_raw": "프로젝트 마일스톤 달성",
    "object_hash": "milestone_001",
    "sender_raw": null,
    "receiver_raw": "팀",
    "receiver_hash": "team_001",
    "confidence": 0.85
  },
  "entities": {
    "team_001": {
      "canonical": "개발팀",
      "variations": ["팀", "team", "개발팀", "우리팀"],
      "type": "group"
    },
    "milestone_001": {
      "canonical": "마일스톤",
      "variations": ["마일스톤", "milestone", "목표"],
      "type": "achievement"
    }
  }
}
```

---

## 🎯 **구현 우선순위**

### Phase 1: 기본 구조 (Week 3-4)
1. ✅ 액탄트 테이블 생성
2. ⬜ 기본 파서 구현 (규칙 기반)
3. ⬜ 엔티티 해시 관리자
4. ⬜ 행동 분류 체계

### Phase 2: 지능형 파싱 (Week 5-6)
1. ⬜ LLM 파싱 통합 (MCP 도구)
2. ⬜ 동일성 판별 알고리즘
3. ⬜ 신뢰도 계산 시스템
4. ⬜ 암묵적 액탄트 추론

### Phase 3: 네트워크 연동 (Week 7-8)
1. ⬜ 액탄트→노드 변환기
2. ⬜ 자동 연관관계 생성
3. ⬜ 인과관계 체인 분석
4. ⬜ 패턴 발견 시스템

---

## 💡 **핵심 이점**

1. **구조화된 이해**: 모든 메모리가 명확한 [주체-행동-객체] 구조
2. **동일성 관리**: 같은 개체를 다르게 표현해도 하나로 인식
3. **관계 추론**: 액탄트 구조로 인과관계 자동 발견
4. **패턴 인식**: 반복되는 행동 패턴 감지
5. **확장 가능**: 6-액탄트 모델로 점진적 확장 가능

---

## 🔧 **다음 단계**

1. DatabaseManager에 액탄트 테이블 추가
2. ActantParser 클래스 구현
3. EntityHashManager 구현
4. 기존 247개 메모리 마이그레이션 도구
5. CLI 명령어 추가 (greeum actant parse)
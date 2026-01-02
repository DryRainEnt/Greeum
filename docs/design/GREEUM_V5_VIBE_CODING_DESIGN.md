# Greeum v5.0 - 바이브코딩 인사이트 축적 시스템

**문서 버전**: 1.0
**작성일**: 2026-01-02
**핵심 전환**: 범용 기억 모듈 → 바이브코딩 개발자를 위한 프로젝트별 경험 축적 시스템

---

## 1. 프로젝트 재정의

### 1.1 기존 vs 신규

| 구분 | v4.0 (기존) | v5.0 (신규) |
|------|-------------|-------------|
| **정의** | LLM을 위한 범용 외부 기억 모듈 | 바이브코딩 개발자를 위한 인사이트 축적 시스템 |
| **타겟** | 모든 LLM 사용자 | AI 코딩으로 여러 프로젝트 만드는 개발자/메이커 |
| **핵심 가치** | "AI가 기억한다" | "지난 프로젝트 경험을 다음에 활용한다" |
| **브랜치** | 자동 맥락 분류 | 명시적 프로젝트 지정 |
| **검색** | Vector 유사도 | Hybrid (Vector + BM25 + 시간) |

### 1.2 타겟 사용자 페르소나

```
이름: 인디 메이커 김개발
도구: Claude Code, Cursor, GitHub Copilot
행동:
  - 동시에 2-5개 프로젝트 진행
  - 빠른 반복, 많은 시행착오
  - 대화로 문제 해결 후 다음으로 넘어감

페인포인트:
  - "이거 저번 프로젝트에서 어떻게 해결했더라?"
  - "그때 Claude가 알려준 방법이 뭐였지?"
  - "같은 에러 또 났는데..."
  - "이 라이브러리 왜 선택했었지?"
```

### 1.3 핵심 가치 제안

```
Before (현재):
  프로젝트 A: CORS 에러 해결 → 대화 종료 → 휘발
  프로젝트 B: (3주 후) CORS 에러... → 처음부터 다시 삽질

After (Greeum v5):
  프로젝트 A: CORS 에러 해결 → Greeum 자동 저장
  프로젝트 B: CORS 에러 → "프로젝트 A에서 해결한 적 있어요: proxy 설정"
```

---

## 2. 핵심 설계 변경

### 2.1 브랜치 = 프로젝트 (명시적 매핑)

**기존 (v4.0):**
```python
# 자동 분류 (모호함)
result = classifier.classify(content)  # LLM이 맥락 판단
branch_id = result.branch_id  # 어느 브랜치인지 불명확
```

**신규 (v5.0):**
```python
# 명시적 프로젝트 지정
greeum.set_project("my-saas-app")
greeum.add("CORS 에러 해결: proxy 설정")

# 또는 호출 시 지정
greeum.add("해결책 내용", project="my-saas-app")
```

**데이터 구조:**
```
projects/
├── my-saas-app/           # 프로젝트 = 브랜치
│   ├── insights/          # 인사이트 블록들
│   │   ├── block_001: "CORS 해결: proxy"
│   │   ├── block_002: "상태관리: Zustand 선택"
│   │   └── block_003: "배포: Vercel edge"
│   └── meta.json          # 프로젝트 메타데이터
├── side-project-b/
└── _cross_project/        # 크로스 프로젝트 인사이트
```

### 2.2 그래프 탐색 + Hybrid 유사도

**원본 설계 준수**: 앵커 기반 그래프 탐색을 유지하면서, 유사도 측정을 Hybrid로 강화

**핵심 아이디어:**
```
전체 인덱스 스캔 (X)
        ↓
앵커에서 시작 → 그래프 따라 DFS → 각 블록에서 Hybrid 유사도 계산 (O)
```

**탐색 흐름:**
```
[쿼리: "CORS 에러 해결"]
         │
         ▼
[앵커 블록에서 시작] ← 프로젝트의 최근 조회/저장 블록
         │
         ▼
[DFS 탐색하며 각 블록과 Hybrid 유사도 계산]
    │
    ├─ Vector: cosine(query_emb, block_emb)
    ├─ BM25: bm25_score(query_keywords, block_keywords)
    └─ Combined: weighted_sum 또는 RRF
         │
         ▼
[유사도 임계값 이상 → 후보 추가]
[유사도 일정 이상 → 해당 방향 더 깊이 탐색]
[유사도 낮음 → 가지치기 (해당 방향 탐색 중단)]
         │
         ▼
[심도 제한까지 반복]
```

**구현:**
```python
def hybrid_graph_search(
    query: str,
    anchor: Block,
    depth: int = 6,
    threshold: float = 0.3,
    explore_threshold: float = 0.15
) -> List[Tuple[Block, float]]:
    """
    앵커에서 시작하여 그래프를 탐색하며 Hybrid 유사도로 후보 수집

    Args:
        query: 검색 쿼리
        anchor: 탐색 시작점 (앵커 블록)
        depth: 최대 탐색 심도
        threshold: 후보 추가 임계값
        explore_threshold: 탐색 확장 임계값 (가지치기 기준)
    """
    # 쿼리 준비
    query_embedding = embed(query)
    query_keywords = tokenize(query)

    visited = set()
    candidates = []

    def dfs(block: Block, current_depth: int):
        if current_depth > depth or block.id in visited:
            return

        visited.add(block.id)

        # === Hybrid 유사도 계산 ===
        vec_sim = cosine_similarity(query_embedding, block.embedding)
        bm25_score = compute_bm25(query_keywords, block.keywords)

        # 가중 평균 (조절 가능)
        hybrid_score = 0.5 * vec_sim + 0.5 * normalize_bm25(bm25_score)

        # 임계값 이상이면 후보에 추가
        if hybrid_score > threshold:
            candidates.append((block, hybrid_score))

        # === 가지치기: 유사도 기반 탐색 확장 결정 ===
        if hybrid_score > explore_threshold:
            # before (이전 블록) 탐색
            if block.before:
                dfs(get_block(block.before), current_depth + 1)

            # after (다음 블록들) 탐색
            for next_id in block.after:
                dfs(get_block(next_id), current_depth + 1)

    # 앵커에서 시작
    dfs(anchor, 0)

    # 유사도 순 정렬
    return sorted(candidates, key=lambda x: x[1], reverse=True)
```

**BM25 인덱스 설계:**
```python
class BM25Index:
    """전체 코퍼스 기반 IDF를 사전 계산하여 개별 블록 점수 계산 지원"""

    def __init__(self, k1: float = 1.5, b: float = 0.75):
        self.k1 = k1
        self.b = b
        self.idf = {}           # 단어별 IDF
        self.doc_count = 0
        self.avg_doc_len = 0
        self.doc_lens = {}      # 문서별 길이

    def add_document(self, doc_id: str, keywords: List[str]):
        """문서 추가 시 IDF 업데이트"""
        self.doc_lens[doc_id] = len(keywords)
        self.doc_count += 1
        self.avg_doc_len = sum(self.doc_lens.values()) / self.doc_count

        for word in set(keywords):
            self.idf[word] = self.idf.get(word, 0) + 1

    def score(self, query_keywords: List[str], block_keywords: List[str]) -> float:
        """개별 블록에 대한 BM25 점수 계산"""
        score = 0
        doc_len = len(block_keywords)

        for word in query_keywords:
            if word not in block_keywords:
                continue

            # IDF
            df = self.idf.get(word, 0)
            idf = log((self.doc_count - df + 0.5) / (df + 0.5) + 1)

            # TF with length normalization
            tf = block_keywords.count(word)
            tf_norm = (tf * (self.k1 + 1)) / (
                tf + self.k1 * (1 - self.b + self.b * doc_len / self.avg_doc_len)
            )

            score += idf * tf_norm

        return score
```

**장점:**
| 항목 | 설명 |
|------|------|
| 원본 설계 준수 | 앵커, 그래프 구조, 심도 제한 유지 |
| 지역성 활용 | 관련 블록들이 그래프상 가까이 있음 |
| Hybrid 정확도 | Vector + BM25로 의미+키워드 모두 포착 |
| 효율적 탐색 | 전체 스캔 대신 그래프 따라 탐색 |
| 가지치기 | 유사도 낮으면 해당 방향 탐색 중단 |

### 2.3 3단계 정확도 파이프라인

**원칙:** 정확도 최우선. 시간은 "힌트", 최종 판단은 LLM.

**문제:**
```
14:00 - "React CORS 해결" (프로젝트 A)
14:10 - "Python 스크립트 에러" (프로젝트 B) ← 시간 가깝지만 다른 맥락!
14:15 - "저녁 뭐 먹지?" ← 완전 다른 주제

→ 시간만으로 판단하면 잘못된 연결
```

**해결: 3단계 파이프라인**
```
[새 인사이트]
      │
      ▼
[1단계: Hybrid Search로 후보 추림]
      │  - Vector + BM25 → 상위 10개
      ▼
[2단계: 확실한 케이스 빠른 처리]
      │
      ├─ 유사도 > 0.85 AND 시간 < 5분 → 자동 연결 (LLM 스킵)
      │
      └─ 그 외 ↓

[3단계: LLM 최종 판단]
      │  - 후보 + 시간 정보 제공
      │  - LLM이 맥락 판단
      ▼
[연결 또는 새 맥락 생성]
```

**구현:**
```python
# 확실한 자동 연결 임계값
AUTO_ATTACH_SIMILARITY = 0.85  # 유사도 85% 이상
AUTO_ATTACH_TIME = 300         # 5분 이내

def store_insight(content: str, project: str = None):
    # 1단계: Hybrid Search로 후보 추림
    candidates = hybrid_search(content, limit=10)
    time_since_last = get_time_since_last_activity(project)

    # 2단계: 확실한 케이스 빠른 처리
    if candidates:
        best = candidates[0]
        if (best.similarity > AUTO_ATTACH_SIMILARITY and
            time_since_last < AUTO_ATTACH_TIME):
            # 매우 확실 → LLM 스킵
            return attach_to(content, best)

    # 3단계: LLM 최종 판단 (시간 정보 포함)
    decision = llm_decide(
        new_content=content,
        candidates=candidates,
        time_context=time_since_last,
        current_project=project
    )

    if decision.create_new:
        return create_new_context(content, project)
    else:
        return attach_to(content, decision.target_block)
```

**LLM 프롬프트:**
```
현재 프로젝트: my-saas-app
마지막 활동: 8분 전

새 인사이트:
"Python 스크립트 에러 해결"

관련 후보 (Hybrid Search 결과):
1. [my-saas-app] "React CORS 해결" (8분 전, 유사도: 0.32)
2. [scripts] "Python 자동화 스크립트" (2일 전, 유사도: 0.78)
3. [my-saas-app] "프로젝트 초기 설정" (1주 전, 유사도: 0.25)

판단 기준:
- 시간이 가까워도 주제가 다르면 다른 맥락
- 유사도가 높으면 시간이 멀어도 같은 맥락일 수 있음

질문: 이 인사이트는 어디에 연결되어야 하나요?
답변 형식: ATTACH:2 또는 NEW_CONTEXT (이유 포함)
```

→ LLM: "ATTACH:2 - Python 관련이므로 scripts 프로젝트의
        Python 자동화 스크립트와 연결. 시간이 가까운 React는
        다른 언어/주제이므로 부적합."

### 2.4 인사이트 필터링

**문제:** 모든 대화 저장 → 노이즈 많음

**해결:** 인사이트만 선별 저장

```python
INSIGHT_PATTERNS = [
    r"해결[했됐]",           # 문제 해결
    r"선택[했한].*이유",      # 의사결정
    r"설정[했한]",           # 설정 변경
    r"에러.*고[쳤침]",       # 에러 수정
    r"배[웠움]",             # 학습
    r"주의.*해야",           # 주의사항
    r"[Ff]ix|[Ss]olve",     # 영어 패턴
]

def is_insight(content: str) -> bool:
    """저장할 가치가 있는 인사이트인지 판단"""
    # 1. 패턴 매칭
    for pattern in INSIGHT_PATTERNS:
        if re.search(pattern, content):
            return True

    # 2. 길이 체크 (너무 짧으면 제외)
    if len(content) < 20:
        return False

    # 3. 인사말/확인 제외
    skip_patterns = [r"^안녕", r"^네[,.]", r"^알겠", r"^감사"]
    for pattern in skip_patterns:
        if re.search(pattern, content):
            return False

    return True  # 기본적으로 저장
```

**수동 저장 옵션:**
```python
# 명시적으로 저장 요청
greeum.add("중요한 인사이트", force=True)

# 또는 MCP에서
add_memory(content="...", force_save=True)
```

---

## 3. API 설계

### 3.1 프로젝트 관리

```
# 프로젝트 목록
GET /projects
Response: ["my-saas-app", "side-project", ...]

# 프로젝트 생성
POST /projects
Body: {"name": "new-project", "description": "설명"}

# 현재 프로젝트 설정
POST /projects/current
Body: {"name": "my-saas-app"}

# 프로젝트 상세
GET /projects/{name}
Response: {"name": "...", "block_count": 42, "last_activity": "..."}
```

### 3.2 인사이트 관리

```
# 인사이트 추가
POST /insights
Body: {
    "content": "CORS 에러는 vite.config.js에 proxy 설정으로 해결",
    "project": "my-saas-app",  # 선택적, 없으면 현재 프로젝트
    "tags": ["cors", "vite"],   # 선택적
    "force": false              # 필터링 우회 여부
}
Response: {
    "success": true,
    "block_id": "abc123",
    "project": "my-saas-app",
    "filtered": false,
    "session_continued": true
}

# 인사이트 검색
POST /insights/search
Body: {
    "query": "CORS 에러",
    "project": null,           # null이면 전체 프로젝트
    "limit": 10,
    "search_mode": "hybrid"    # "hybrid" | "vector" | "keyword"
}
Response: {
    "results": [
        {
            "block_id": "abc123",
            "content": "CORS 에러는 vite.config.js에...",
            "project": "my-saas-app",
            "timestamp": "2026-01-02T14:30:00",
            "relevance": {
                "combined": 0.85,
                "vector": 0.72,
                "bm25": 0.91,
                "recency": 0.65
            }
        }
    ],
    "search_stats": {
        "mode": "hybrid",
        "projects_searched": 3,
        "total_candidates": 150,
        "elapsed_ms": 45
    }
}
```

### 3.3 크로스 프로젝트 검색

```
# 모든 프로젝트에서 검색
POST /insights/search
Body: {
    "query": "상태관리 라이브러리",
    "project": null,  # 전체 검색
    "group_by_project": true
}
Response: {
    "results_by_project": {
        "my-saas-app": [
            {"content": "Zustand 선택 - 간단해서", ...}
        ],
        "side-project": [
            {"content": "Redux 사용 - 팀 협업용", ...}
        ]
    }
}
```

### 3.4 MCP 도구 인터페이스

```python
# 기존 호환 유지 + 프로젝트 파라미터 추가
tools = [
    {
        "name": "add_memory",
        "description": "프로젝트에 인사이트 저장",
        "parameters": {
            "content": {"type": "string", "required": True},
            "project": {"type": "string", "required": False},
            "importance": {"type": "number", "default": 0.5}
        }
    },
    {
        "name": "search_memory",
        "description": "인사이트 검색 (프로젝트 내 또는 전체)",
        "parameters": {
            "query": {"type": "string", "required": True},
            "project": {"type": "string", "required": False},
            "limit": {"type": "integer", "default": 5}
        }
    },
    {
        "name": "set_project",
        "description": "현재 작업 프로젝트 설정",
        "parameters": {
            "name": {"type": "string", "required": True}
        }
    },
    {
        "name": "list_projects",
        "description": "프로젝트 목록 조회",
        "parameters": {}
    }
]
```

---

## 4. 아키텍처

### 4.1 컴포넌트 구조

```
greeum/
├── core/
│   ├── project_manager.py      # 🆕 프로젝트 관리
│   ├── hybrid_search.py        # 🆕 Hybrid Search 엔진
│   ├── bm25_index.py           # 🆕 BM25 인덱스
│   ├── rrf_fusion.py           # 🆕 RRF 융합 로직
│   ├── session_tracker.py      # 🆕 시간 기반 세션
│   ├── insight_filter.py       # 🆕 인사이트 필터링
│   ├── block_manager.py        # 기존 (수정)
│   ├── vector_index.py         # 기존 유지
│   └── ...
├── server/
│   ├── routes/
│   │   ├── projects.py         # 🆕 프로젝트 API
│   │   ├── insights.py         # 🆕 인사이트 API (기존 memory 대체)
│   │   └── ...
│   └── ...
└── mcp/
    └── tools.py                # 수정: 프로젝트 파라미터 추가
```

### 4.2 데이터 흐름

```
[사용자: "이 CORS 에러 어떻게 해결했더라?"]
         │
         ▼
[MCP: search_memory(query="CORS 에러")]
         │
         ▼
[HybridSearch]
    ├── Vector Search ──────┐
    │   (의미: "CORS 관련") │
    │                       ├──▶ [RRF Fusion] ──▶ 순위 통합
    └── BM25 Search ────────┘
        (키워드: "CORS", "에러")
         │
         ▼
[프로젝트별 그룹화]
         │
         ▼
[응답: "프로젝트 A에서 해결한 적 있어요:
        vite.config.js에 proxy 설정"]
```

### 4.3 저장 흐름

```
[Claude: "CORS 에러는 proxy 설정으로 해결됩니다"]
         │
         ▼
[인사이트 필터] ──── "해결" 패턴 감지 ✓
         │
         ▼
[세션 체크] ──── 마지막 활동 5분 전 → 같은 세션
         │
         ▼
[프로젝트 확인] ──── 현재: "my-saas-app"
         │
         ▼
[블록 연결] ──── 마지막 블록에 연결 (세션 연속)
         │
         ▼
[인덱스 업데이트]
    ├── Vector Index (FAISS)
    └── BM25 Index
         │
         ▼
[저장 완료]
```

---

## 5. 구현 우선순위

### Phase 1: 그래프 탐색 + Hybrid 유사도 (1주)

1. **BM25 인덱스**
   - `bm25_index.py` 구현
   - 전체 코퍼스 IDF 사전 계산
   - 한국어 토크나이저 (konlpy 또는 mecab)
   - 블록 추가 시 인덱스 업데이트

2. **Hybrid 그래프 탐색**
   - `hybrid_graph_search.py` 구현
   - 앵커에서 DFS 시작
   - 각 블록에서 Vector + BM25 점수 계산
   - 가지치기 로직 (explore_threshold)

3. **앵커 관리**
   - 프로젝트별 앵커 블록 추적
   - 조회/저장 시 앵커 갱신
   - 원본 설계 "최근 조회된 블록을 앵커로" 준수

### Phase 2: 3단계 파이프라인 (1주)

4. **LLM 판단 모듈**
   - `llm_classifier.py` 개선
   - Hybrid 후보 기반 프롬프트
   - 시간 컨텍스트 포함

5. **자동 연결 로직**
   - 유사도 > 0.85 AND 시간 < 5분 → 스킵
   - 그 외 → LLM 판단

6. **프로젝트 관리**
   - `project_manager.py` 구현
   - 프로젝트 = 브랜치 매핑
   - 현재 프로젝트 추적

### Phase 3: 품질 개선 (1주)

7. **인사이트 필터링**
   - `insight_filter.py` 구현
   - 패턴 기반 + 길이 기반
   - force 옵션

8. **API 업데이트**
   - 프로젝트 엔드포인트
   - 크로스 프로젝트 검색
   - MCP 도구 업데이트

9. **정확도 모니터링**
   - 연결 정확도 로깅
   - LLM 판단 이유 저장
   - 피드백 루프 준비

---

## 6. 성공 지표

### 6.1 기능 지표

| 지표 | 목표 |
|------|------|
| 같은 세션 연결 정확도 | > 95% |
| 크로스 프로젝트 검색 정확도 | > 80% |
| 인사이트 필터 정밀도 | > 85% |
| API 응답 시간 | < 300ms |

### 6.2 사용자 경험 지표

```
목표 시나리오:

1. 사용자가 "저번에 CORS 어떻게 해결했지?" 질문
2. Greeum이 3초 내 관련 인사이트 제시
3. 사용자가 "아, 그거!" 하고 바로 적용
4. 삽질 시간 30분 → 3분으로 단축
```

---

## 7. 기존 설계와의 호환성

### 7.1 유지되는 것

- 블록 구조 (before/after 연결)
- SQLite 저장소
- MCP 인터페이스 기본 형태
- STM 캐시 개념 (3슬롯)

### 7.2 변경되는 것

| 기존 | 신규 |
|------|------|
| 자동 브랜치 분류 | 명시적 프로젝트 지정 |
| Vector 유사도만 | Hybrid Search |
| 모든 내용 저장 | 인사이트 필터링 |
| 브랜치 ID (해시) | 프로젝트 이름 (문자열) |

### 7.3 마이그레이션

```python
# 기존 브랜치 → 프로젝트 변환
def migrate_branches_to_projects():
    for branch in get_all_branches():
        # 브랜치 내 블록들의 공통 키워드로 프로젝트명 추론
        project_name = infer_project_name(branch)
        # 또는 수동 매핑 요청
        rename_branch_to_project(branch.id, project_name)
```

---

## 8. 원본 설계 원칙 준수

사업화문서.txt 원칙과의 정합성:

| 원본 요구사항 | v5.0 적용 | 구현 |
|---------------|-----------|------|
| "동일 맥락 → 동일 브랜치" | ✅ | 프로젝트 = 브랜치 |
| "최근 조회 블록을 앵커로" | ✅ | 프로젝트별 앵커 관리, 조회/저장 시 갱신 |
| "앵커에서 탐색 시작" | ✅ | `hybrid_graph_search(anchor)` |
| "탐색 심도 인자 전달" | ✅ | `depth` 파라미터 |
| "유사한 블록 찾기" | ✅ | Hybrid 유사도 (Vector + BM25) |
| "조회 후 저장" | ✅ | 그래프 탐색 → LLM 판단 → 연결 |
| "before/after 연결" | ✅ | 그래프 구조 유지 |
| "순환 참조 방지" | ✅ | visited set |
| "시점 기반 끼워넣기" | ⚠️ | LLM이 판단 (명시적 시점 로직은 없음) |
| "객관적 지식 갱신" | ⚠️ | 향후 구현 (선택적 갱신 옵션) |
| "사용자 경험 기준" | ✅ | "삽질 시간 단축" 명확한 가치 |

---

**문서 끝**

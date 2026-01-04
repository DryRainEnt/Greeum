# Greeum Legacy Design Notes

> **목적**: 구버전 설계 문서들의 핵심 인사이트를 보존하기 위한 아카이브
> **생성일**: 2026-01-04
> **현재 버전**: v5.1.0

---

## 1. 아키텍처 진화 요약

### 버전 히스토리
| 버전 | 핵심 변화 | 시기 |
|------|----------|------|
| v2.x | 기본 블록체인 메모리, FAISS 벡터 검색 | 2024 |
| v3.0 | 브랜치 기반 메모리, 액탄트 모델 도입 | 2025 초 |
| v4.0 | InsightJudge, HybridGraphSearch | 2025 중 |
| v5.0 | REST API, 원격 서버 지원 | 2026 |

---

## 2. 핵심 설계 결정

### 2.1 브랜치 기반 메모리 시스템
**출처**: `branch_optimization_final_review.md`

```
그래프 기반 → 브랜치 기반 전환

핵심 구조:
- root: 브랜치 루트 (프로젝트)
- before: 부모 블록
- after: 자식 블록들

성과:
- 로컬 히트율: 62-68% → 100%
- 평균 홉 수: 23.0 → 6.0 (-73.9%)
- 검색 시간: 0.05ms → 0.03ms
```

**최적화 파라미터**:
```python
DEPTH_DEFAULT = 6      # 기존 3에서 확장
K_DEFAULT = 20         # 기존 8에서 확장
SIMILARITY_THRESHOLD = 0.02  # 기존 0.1에서 완화
```

### 2.2 STM 슬롯 시스템
- A/B/C 3개 슬롯으로 병렬 작업 브랜치 관리
- 유사도 기반 자동 슬롯 라우팅 (임계값 0.4)
- 슬롯별 독립적 컨텍스트 유지

### 2.3 DFS 로컬 우선 검색
```python
# 양방향 탐색: 자식 + 부모 + 형제 노드
# 스코어링: Jaccard + 키워드 보너스 + 부분 매칭 + 로컬리티 보너스

# 로컬 히트 조건 (개선됨)
local_hit_threshold = max(3, k // 3)
if len(results) >= local_hit_threshold or high_quality >= 2:
    search_type = 'dfs_local'
```

---

## 3. 액탄트 모델 (Actant Model)

**출처**: `GREEUM_V3.0.0_ACTANT_SCHEMA_DESIGN.md`, `actant_identity_system_design.md`

### 그레마스 6 액탄트
| 역할 | 설명 | 예시 |
|------|------|------|
| Subject | 행위 주체 | 사용자, Claude, 팀 |
| Object | 행위 대상 | 프로젝트, 기능, 버그 |
| Sender | 행위 발신자 | 요청자, 의뢰인 |
| Receiver | 행위 수신자 | 수혜자, 담당자 |
| Helper | 조력자 | 도구, 라이브러리 |
| Opponent | 방해자 | 제약, 버그, 한계 |

### 메모리 저장 패턴
```
[주체-행동-객체] 구조의 1-2문장
예: [사용자-요청-MCP도구테스트] 연결된 도구 파악 및 테스트 진행
예: [Claude-발견-TypeScript오류] src/types/session.ts의 processId 타입 불일치
```

### 동일성 해시 시스템
```python
subject_hashes = {
    "user": ["사용자", "유저", "나", "내가", "user"],
    "claude": ["Claude", "claude", "AI", "어시스턴트"],
    "system": ["시스템", "system", "서버", "프로그램"]
}
```

---

## 4. Native MCP 서버 설계

**출처**: `NATIVE_MCP_DESIGN_SPEC.md`

### 설계 배경
- FastMCP AsyncIO 충돌 문제 해결
- Windows/macOS/Linux/WSL 완전 호환

### 아키텍처
```
greeum/mcp/native/
├── server.py      # 메인 서버 클래스
├── transport.py   # STDIO 전송 계층
├── protocol.py    # JSON-RPC 메시지 처리
├── tools.py       # MCP 도구 정의
└── types.py       # Pydantic 타입 정의
```

### 핵심 기술
- `anyio` 기반 안전한 AsyncIO 처리
- `asyncio.run()` 충돌 완전 회피
- UTF-8 인코딩으로 Windows 호환성 보장

---

## 5. 미래 방향 (미구현 설계)

### 5.1 계층적 다중참조 메모리
**출처**: `hierarchical_memory_design.md`

```sql
-- 계층적 관계 테이블
CREATE TABLE block_hierarchies (
    parent_block_index INTEGER,
    child_block_index INTEGER,
    relationship_type TEXT,  -- 'cluster', 'reference', 'temporal'
    relationship_strength REAL
);

-- 클러스터 정의
CREATE TABLE memory_clusters (
    cluster_name TEXT,
    anchor_block_index INTEGER,
    keywords TEXT,  -- JSON array
    context_vector BLOB
);
```

**기대 효과**:
- 하나의 기억이 여러 맥락에 속함
- 앵커 블록에서 BFS로 계층적 탐색
- 클러스터 간 중복 제거 및 랭킹

### 5.2 인과관계 기반 메모리 연결
**출처**: `causality_technical_feasibility_report.md`

**목표**:
- 양방향 인과관계 감지 (A→B, B→A)
- 다층 인과관계 추적 (A→B→C→D)
- 신뢰도 점수 정량화 (0.0~1.0)

**기술 스택**:
```
1단계: 패턴 매칭 (정규표현식)
2단계: 의미적 분석 (BERT/RoBERTa)
3단계: 종합 판단 (가중 평균)
  - 시간적 25% + 언어적 35% + 의미적 25% + 문맥적 15%
```

**복잡도**: ★★★★★ (최고 난이도)
**실현 가능성**: ★★★★☆ (높음)

### 5.3 장기 로드맵 비전
**출처**: `GREEUM_V3.0.0_LONGTERM_ROADMAP.md`

```
v3.0.0 비전: "텍스트 저장소에서 지능형 사고 파트너로"

핵심 목표:
- 구조화된 지식: 액탄트 모델 기반 의미 파싱
- 인과관계 추론: 80%+ 정확도의 논리적 연결
- 맥락적 이해: 시간/공간/의도 종합 분석
- 능동적 제안: 패턴 학습 기반 인사이트 제공
```

---

## 6. 성능 벤치마크 기준

### 검색 성능
| 지표 | Legacy | Optimized |
|------|--------|-----------|
| 로컬 히트율 | 62-68% | 100% |
| 평균 홉 수 | 23.0 | 6.0 |
| 검색 시간 | 0.05ms | 0.03ms |
| 캐시 히트율 | N/A | 33.1% |

### 시스템 요구사항
- 200블록까지 선형 성능 유지
- 검색 처리 <100ms 목표
- 메모리 추가 시 즉시 인덱싱

---

## 7. 삭제된 레거시 코드 참조

### 마이그레이션 스크립트 (v5.1.0에서 삭제)
- `embedding_migration_v2.py`
- `migrate_embeddings.py`
- `unify_embeddings.py`
- `merge_memory_databases.py`

### 구버전 모듈 (v5.1.0에서 삭제)
- `greeum/embedding_models_optimized.py`
- `greeum/core/v3_memory_core.py`
- `greeum/api/anchors_simple.py`

---

*이 문서는 Greeum 프로젝트의 설계 히스토리와 미래 방향을 기록합니다.*
*구체적인 구현 방법은 해당 버전의 소스 코드를 참조하세요.*

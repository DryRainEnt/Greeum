# 🔗 Greeum 앵커 시스템 사용자 가이드

**Version**: v2.2.5a1  
**Updated**: 2025-08-28

## 📖 목차

- [개요](#개요)
- [앵커 시스템이란?](#앵커-시스템이란)
- [CLI 사용법](#cli-사용법)
- [REST API 사용법](#rest-api-사용법)
- [실전 예제](#실전-예제)
- [고급 사용법](#고급-사용법)
- [문제 해결](#문제-해결)

## 개요

Greeum의 앵커 시스템은 **3-slot STM(Short-Term Memory) 구조**를 통해 컨텍스트 기반의 지능형 메모리 탐색을 제공합니다. 기존의 전역 검색과 달리, 특정 주제나 맥락을 중심으로 **국소적 그래프 탐색**을 수행하여 더 관련성 높고 빠른 메모리 검색을 가능하게 합니다.

## 앵커 시스템이란?

### 🎯 핵심 개념

**앵커(Anchor)**는 현재 관심 주제를 나타내는 메모리 블록에 대한 참조점입니다. 3개의 슬롯(A, B, C)으로 구성되어 다차원적 컨텍스트를 동시에 관리할 수 있습니다.

### 📍 3-Slot 구조

| 슬롯 | 역할 | 홉 예산 | 용도 |
|------|------|---------|------|
| **A** | 주요 맥락 | 1홉 | 현재 대화 주제, 즉시적 컨텍스트 |
| **B** | 보조 맥락 | 2홉 | 관련 주제, 중간 범위 탐색 |
| **C** | 확장 맥락 | 3홉 | 배경 지식, 깊은 연관 탐색 |

### 🔍 작동 원리

1. **앵커 설정**: 특정 메모리 블록을 앵커로 설정
2. **국소 탐색**: 앵커 주변 N홉 이내의 관련 블록들만 검색
3. **Fallback**: 국소 검색 실패 시 자동으로 전역 검색으로 확장
4. **자동 이동**: 검색 패턴에 따라 앵커가 자동으로 최적 위치로 이동

## CLI 사용법

### 📋 앵커 상태 확인

```bash
greeum anchors status
```

**출력 예시:**
```
⚓ Anchor Status Report
==================================================

🔹 Slot A: 📌 PINNED
   Anchor Block: #580
   Hop Budget: 3
   Last Used: 2025-08-15 17:06:05
   Summary: API 개발 관련 메모리

🔹 Slot B: 🔄 Active
   Anchor Block: #127
   Hop Budget: 2
   Last Used: 2025-08-18 01:24:39
   Summary: 데이터베이스 설계 논의

🔹 Slot C: 🔄 Active
   Anchor Block: #89
   Hop Budget: 3
   Last Used: 2025-08-18 01:24:39
   Summary: 성능 최적화 관련
```

### 🎯 앵커 설정

```bash
# 특정 블록을 슬롯 A에 앵커로 설정
greeum anchors set A 1234

# 사용자 정의 요약과 홉 예산으로 설정
greeum anchors set B 5678 --summary "머신러닝 프로젝트" --hop-budget 2
```

### 📌 앵커 고정/해제

```bash
# 앵커 고정 (자동 이동 방지)
greeum anchors pin A

# 앵커 고정 해제 (자동 이동 허용)
greeum anchors unpin A

# 앵커 삭제
greeum anchors clear A
```

### 🔍 앵커 기반 검색

```bash
# 슬롯 A 기반 국소 검색 (반경: 2홉)
greeum search "기계학습 알고리즘" --slot A --radius 2

# 여러 슬롯에서 검색
greeum search "데이터 분석" --slot B --radius 1 --fallback

# 기존 검색 (앵커 사용 안함)
greeum search "일반 검색어"
```

## REST API 사용법

### 📊 앵커 상태 조회

```bash
curl -X GET "http://localhost:5000/v1/anchors"
```

**응답 예시:**
```json
{
  "version": 1,
  "slots": [
    {
      "slot": "A",
      "anchor_block_id": "1234",
      "hop_budget": 3,
      "pinned": true,
      "last_used_ts": 1693555200,
      "summary": "API 개발 관련 메모리"
    },
    {
      "slot": "B",
      "anchor_block_id": "5678",
      "hop_budget": 2,
      "pinned": false,
      "last_used_ts": 1693555100,
      "summary": "데이터베이스 설계"
    }
  ],
  "updated_at": 1693555300,
  "timestamp": "2025-08-28T12:00:00"
}
```

### ⚙️ 앵커 업데이트

```bash
# 앵커 블록 변경
curl -X PATCH "http://localhost:5000/v1/anchors/A" \
     -H "Content-Type: application/json" \
     -d '{
       "anchor_block_id": "9999",
       "summary": "새로운 프로젝트 시작",
       "hop_budget": 2
     }'

# 앵커 고정
curl -X PATCH "http://localhost:5000/v1/anchors/B" \
     -H "Content-Type: application/json" \
     -d '{"pinned": true}'
```

### 🔍 앵커 기반 검색 API

```bash
# 슬롯 A 기반 검색
curl -X GET "http://localhost:5000/api/v1/search?query=머신러닝&slot=A&radius=2&limit=5"

# 결과 예시
{
  "results": [
    {
      "block_index": 1234,
      "context": "머신러닝 알고리즘 구현 방법...",
      "relevance_score": 0.95
    }
  ],
  "metadata": {
    "local_search_used": true,
    "local_results": 3,
    "fallback_used": false
  },
  "search_type": "anchor_based",
  "slot": "A",
  "radius": 2
}
```

## 실전 예제

### 🧠 시나리오 1: 개발 프로젝트 관리

```bash
# 1. 프로젝트 시작 - API 설계 블록을 앵커로 설정
greeum anchors set A 1001 --summary "RESTful API 설계"

# 2. 관련 검색 - 앵커 주변에서 관련 내용 찾기
greeum search "인증 방법" --slot A --radius 2

# 3. 보조 맥락 설정 - 데이터베이스 관련
greeum anchors set B 2002 --summary "PostgreSQL 스키마"

# 4. 다차원 검색
greeum search "사용자 권한" --slot A  # API 맥락에서
greeum search "사용자 권한" --slot B  # DB 맥락에서
```

### 📚 시나리오 2: 연구 논문 정리

```bash
# 1. 주요 논문을 앵커로 설정
greeum anchors set A 3001 --summary "Transformer 아키텍처 논문"
greeum anchors pin A  # 고정하여 자동 이동 방지

# 2. 관련 논문들 탐색
greeum search "attention mechanism" --slot A --radius 3

# 3. 보조 주제 설정
greeum anchors set B 3002 --summary "BERT 모델 구현"

# 4. 비교 분석
greeum search "self-attention" --slot A  # Transformer 관점
greeum search "self-attention" --slot B  # BERT 관점
```

## 고급 사용법

### 🔄 자동 앵커 이동

앵커는 검색 패턴에 따라 자동으로 최적 위치로 이동합니다:

```python
# Python API 예제
from greeum.anchors.auto_movement import AutoAnchorMovement

auto_movement = AutoAnchorMovement(anchor_manager, links_cache, db_manager)

# 주제 변화 감지 및 앵커 이동 평가
evaluation = auto_movement.evaluate_anchor_movement(
    slot='A',
    search_results=recent_search_results,
    query_topic_vec=new_topic_embedding
)

if evaluation['should_move']:
    print(f"앵커 이동 권장: {evaluation['reason']}")
```

### 📊 성능 모니터링

```bash
# 앵커 사용 통계 확인 (향후 구현 예정)
greeum anchors stats

# 검색 성능 비교
greeum search "테스트 쿼리"           # 전역 검색
greeum search "테스트 쿼리" --slot A  # 앵커 검색 (더 빠름)
```

### ⚡ 성능 최적화 팁

1. **적절한 홉 예산**: 작은 홉(1-2)으로 시작해서 필요시 확장
2. **앵커 고정**: 안정된 주제는 pin으로 고정
3. **슬롯 활용**: A(즉시), B(중간), C(배경) 역할 분담
4. **Fallback 활용**: `--fallback` 옵션으로 완전성 보장

## 문제 해결

### ❌ 일반적인 문제들

**Q: "Anchors not initialized" 오류가 발생해요**
```bash
# A: Bootstrap 스크립트 실행
python scripts/bootstrap_graphindex.py
```

**Q: 앵커 검색 결과가 없어요**
```bash
# A: Fallback 옵션 사용 또는 반경 확장
greeum search "쿼리" --slot A --radius 3 --fallback
```

**Q: 앵커가 자동으로 이동해서 혼란스러워요**
```bash
# A: 중요한 앵커는 고정하세요
greeum anchors pin A
```

**Q: 성능이 기대만큼 빠르지 않아요**
```bash
# A: 홉 예산을 줄이고 적절한 슬롯 사용
greeum search "쿼리" --slot A --radius 1  # 더 빠름
```

### 🔧 고급 문제 해결

**앵커 파일 손상 시:**
```bash
# 백업에서 복원
cp data/anchors_backup.json data/anchors.json

# 또는 재초기화
rm data/anchors.json
python scripts/bootstrap_graphindex.py
```

**그래프 인덱스 재구성:**
```bash
# 그래프 재구성 (시간 소요)
rm data/graph_snapshot.jsonl
python scripts/bootstrap_graphindex.py --rebuild-graph
```

## 🎯 다음 단계

- [API Reference](api-reference.md) - 상세한 API 문서
- [Architecture Design](design/anchorized-memory.md) - 시스템 설계 문서
- [Performance Guide](performance-guide.md) - 성능 최적화 가이드

---

💡 **팁**: 앵커 시스템은 기존 Greeum 기능과 완전히 호환됩니다. 앵커를 사용하지 않아도 모든 기능이 정상적으로 동작합니다!
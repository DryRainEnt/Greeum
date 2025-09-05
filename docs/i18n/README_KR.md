# 🧠 Greeum v2.2.5

<p align="center">
  <a href="../../README.md">🇰🇷 한국어</a> |
  <a href="README_EN.md">🇺🇸 English</a> |
  <a href="README_ZH.md">🇨🇳 中文</a> |
  <a href="README_JP.md">🇯🇵 日本語</a> |
  <a href="README_ES.md">🇪🇸 Español</a> |
  <a href="README_DE.md">🇩🇪 Deutsch</a> |
  <a href="README_FR.md">🇫🇷 Français</a>
</p>

다국어 지원 LLM 독립적인 기억 관리 시스템

## 📌 개요

**Greeum** (발음: 그리음)은 모든 LLM(대규모 언어 모델)에 연결할 수 있는 **범용 기억 모듈**로서 다음과 같은 기능을 제공합니다:
- 사용자의 발화, 목표, 감정, 의도 등 장기적인 기록 추적
- 현재 맥락과 관련된 기억 회상
- 다국어 환경에서의 시간 표현 인식 및 처리
- "기억을 가진 AI"로서의 기능

Greeum은 RAG(Retrieval-Augmented Generation) 아키텍처에 기반한 LLM 독립적 메모리 시스템입니다. 정보 저장 및 검색(block_manager.py), 관련 기억 관리(cache_manager.py), 프롬프트 증강(prompt_wrapper.py) 등 RAG의 핵심 구성 요소를 구현하여 더 정확하고 맥락에 맞는 응답을 생성합니다.

이름 "Greeum"은 한국어 "그리움"에서 영감을 받았으며, 기억 시스템의 본질을 완벽하게 담고 있습니다.

## 🔑 주요 기능

- **블록체인 유사 구조의 장기 기억(LTM)**: 불변성을 가진 블록 단위 메모리 저장소
- **TTL 기반의 단기 기억(STM)**: 일시적으로 중요한 정보를 효율적으로 관리
- **의미적 연관성**: 키워드/태그/벡터 기반 기억 회상 시스템
- **웨이포인트 캐시**: 현재 맥락과 관련된 기억을 자동으로 검색
- **프롬프트 조합기**: 관련 기억을 포함한 LLM 프롬프트 자동 생성
- **시간적 추론기**: 다국어 환경에서 고급 시간 표현 인식 처리
- **다국어 지원**: 한국어, 영어 등 자동 언어 감지 및 처리
- **Model Control Protocol**: [GreeumMCP](https://github.com/DryRainEnt/GreeumMCP) 별도 패키지를 통해 Cursor, Unity, Discord 등 외부 도구 연동 지원

## ⚙️ 설치 방법

1. 저장소 복제
   ```bash
   git clone https://github.com/DryRainEnt/Greeum.git
   cd Greeum
   ```

2. 의존성 설치 (v2.2.5 - 앵커 시스템 포함)
   ```bash
   pip install "greeum>=2.2.5"
   
   # 또는 모든 기능 포함 설치
   pip install "greeum[all]>=2.2.5"
   ```

## 🧪 사용 방법

### CLI 인터페이스

```bash
# 장기 기억 추가
python cli/memory_cli.py add -c "새로운 프로젝트를 시작했고 정말 흥미로워요"

# 키워드로 기억 검색
python cli/memory_cli.py search -k "프로젝트,흥미로운"

# 시간 표현으로 기억 검색
python cli/memory_cli.py search-time -q "3일 전에 무엇을 했지?" -l "ko"

# 단기 기억 추가
python cli/memory_cli.py stm "오늘 날씨가 좋네요"

# 단기 기억 조회
python cli/memory_cli.py get-stm

# 프롬프트 생성
python cli/memory_cli.py prompt -i "프로젝트는 어떻게 진행되고 있나요?"
```

### REST API 서버

```bash
# API 서버 실행
python api/memory_api.py
```

웹 인터페이스: http://localhost:5000

API 엔드포인트:
- GET `/api/v1/health` - 상태 확인
- GET `/api/v1/blocks` - 블록 목록 조회
- POST `/api/v1/blocks` - 블록 추가
- GET `/api/v1/search?keywords=keyword1,keyword2` - 키워드 검색
- GET `/api/v1/search/time?query=yesterday&language=en` - 시간 표현 검색
- GET, POST, DELETE `/api/v1/stm` - 단기 기억 관리
- POST `/api/v1/prompt` - 프롬프트 생성
- GET `/api/v1/verify` - 블록체인 무결성 검증

### Python 라이브러리

```python
from greeum import BlockManager, STMManager, CacheManager, PromptWrapper
from greeum.text_utils import process_user_input
from greeum.temporal_reasoner import TemporalReasoner

# 사용자 입력 처리
user_input = "새로운 프로젝트를 시작했고 정말 흥미로워요"
processed = process_user_input(user_input)

# 블록 매니저로 기억 저장
block_manager = BlockManager()
block = block_manager.add_block(
    context=processed["context"],
    keywords=processed["keywords"],
    tags=processed["tags"],
    embedding=processed["embedding"],
    importance=processed["importance"]
)

# 시간 기반 검색 (다국어)
temporal_reasoner = TemporalReasoner(db_manager=block_manager, default_language="auto")
time_query = "3일 전에 무엇을 했지?"
time_results = temporal_reasoner.search_by_time_reference(time_query)

# 프롬프트 생성
cache_manager = CacheManager(block_manager=block_manager)
prompt_wrapper = PromptWrapper(cache_manager=cache_manager)

user_question = "프로젝트는 어떻게 진행되고 있나요?"
prompt = prompt_wrapper.compose_prompt(user_question)

# LLM에 전달
# llm_response = call_your_llm(prompt)
```

## 🧱 아키텍처

```
greeum/
├── greeum/                # 핵심 라이브러리
│   ├── block_manager.py    # 장기 기억 관리
│   ├── stm_manager.py      # 단기 기억 관리
│   ├── cache_manager.py    # 웨이포인트 캐시
│   ├── prompt_wrapper.py   # 프롬프트 조합
│   ├── text_utils.py       # 텍스트 처리 유틸리티
│   ├── temporal_reasoner.py # 시간 기반 추론
│   ├── embedding_models.py  # 임베딩 모델 통합
├── api/                   # REST API 인터페이스
├── cli/                   # 명령줄 도구
├── data/                  # 데이터 저장 디렉토리
├── tests/                 # 테스트 스위트
```

## 브랜치 관리 규칙

- **main**: 안정적인 릴리즈 버전 브랜치
- **dev**: 핵심 피쳐 개발 브랜치 (개발 후 테스트 검증이 완료되면 main으로 머지)
- **test-collect**: 성능 지표 및 A/B 테스트 데이터 수집용 브랜치

## 📊 성능 테스트

Greeum은 다음과 같은 영역에서 성능 테스트를 진행합니다:

### T-GEN-001: 응답의 구체성 증가율
- Greeum 메모리 활용 시 응답 품질 향상도 측정
- 평균 18.6% 품질 향상 확인
- 구체적 정보 포함량 4.2개 증가

### T-MEM-002: 메모리 검색 Latency
- 웨이포인트 캐시를 통한 검색 속도 향상 측정
- 평균 5.04배 속도 향상 확인
- 1,000개 이상 메모리 블록에서 최대 8.67배 속도 개선

### T-API-001: API 호출 효율성
- 기억 기반 맥락 제공으로 인한 재질문 감소율 측정
- 재질문 필요성 78.2% 감소 확인
- API 호출 횟수 감소로 비용 절감 효과

## 📊 메모리 블록 구조

```json
{
  "block_index": 143,
  "timestamp": "2025-05-08T01:02:33",
  "context": "새로운 프로젝트를 시작했고 정말 흥미로워요",
  "keywords": ["프로젝트", "시작", "흥미로운"],
  "tags": ["긍정적", "시작", "동기부여"],
  "embedding": [0.131, 0.847, ...],
  "importance": 0.91,
  "hash": "...",
  "prev_hash": "..."
}
```

## 🔤 지원 언어

Greeum은 다음 언어의 시간 표현 인식을 지원합니다:
- 🇰🇷 한국어: 한국어 시간 표현 기본 지원 (어제, 지난주, 3일 전 등)
- 🇺🇸 영어: 영어 시간 형식 완전 지원 (yesterday, 3 days ago 등)
- 🌐 자동 감지: 언어를 자동으로 감지하고 적절히 처리

## 🔍 시간적 추론 예시

```python
# 한국어
result = evaluate_temporal_query("3일 전에 뭐 했어?", language="ko")
# 반환값: {detected: True, language: "ko", best_ref: {term: "3일 전"}}

# 영어
result = evaluate_temporal_query("What did I do 3 days ago?", language="en")
# 반환값: {detected: True, language: "en", best_ref: {term: "3 days ago"}}

# 자동 감지
result = evaluate_temporal_query("What happened yesterday?")
# 반환값: {detected: True, language: "en", best_ref: {term: "yesterday"}}
```

## 🔧 프로젝트 확장 계획

- **Model Control Protocol**: MCP 지원에 대해서는 [GreeumMCP](https://github.com/DryRainEnt/GreeumMCP) 레포지토리를 확인하세요 - Greeum을 Cursor, Unity, Discord 등의 도구와 연결할 수 있는 별도의 패키지입니다
- **다국어 지원 강화**: 일본어, 중국어, 스페인어 등 추가 언어 지원
- **임베딩 개선**: 실제 임베딩 모델 통합 (예: sentence-transformers)
- **키워드 추출 향상**: 언어별 키워드 추출 구현
- **클라우드 통합**: 데이터베이스 백엔드 추가 (SQLite, MongoDB 등)
- **분산 처리**: 대규모 메모리 관리를 위한 분산 처리 구현

## 🌐 웹사이트

웹사이트 방문: [greeum.app](https://greeum.app)

## 📄 라이선스

MIT License

## 👥 기여

버그 보고, 기능 제안, 풀 리퀘스트 등 모든 기여를 환영합니다!

## 📱 연락처

이메일: playtart@play-t.art 
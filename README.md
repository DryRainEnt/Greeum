# 🧠 MemoryBlockEngine v0.2

LLM(대규모 언어 모델) 독립 기억 시스템 통합 라이브러리

## 📌 개요

**MemoryBlockEngine**은 어떤 LLM 모델에도 부착할 수 있는 **범용 기억 모듈**로,  
- 사용자의 장기적 발화/목표/감정/의도를 추적하고,  
- 현재 문맥에 적합한 기억을 회상하며,  
- 결과적으로 "기억을 가진 AI"처럼 동작할 수 있도록 설계되었습니다.

## 🔑 주요 기능

- **장기 기억 블록**: 블록체인 유사 구조로 불변성 있는 기억 저장
- **단기 기억 관리**: TTL(Time-To-Live) 구조의 유동적 단기 기억
- **의미 중심 연상**: 키워드/태그/벡터 기반 기억 회상 시스템
- **웨이포인트 캐시**: 현재 문맥과 관련된 기억을 자동으로 검색
- **프롬프트 조합**: 관련 기억을 포함한 LLM 프롬프트 자동 생성

## ⚙️ 설치 방법

1. 저장소 클론
   ```bash
   git clone https://github.com/yourusername/memory-block-engine.git
   cd memory-block-engine
   ```

2. 의존성 설치
   ```bash
   pip install -r requirements.txt
   ```

## 🧪 사용 방법

### CLI 인터페이스

```bash
# 장기 기억 추가
python cli/memory_cli.py add -c "새 프로젝트를 시작했는데 너무 재미있다"

# 키워드로 기억 검색
python cli/memory_cli.py search -k "프로젝트,시작"

# 단기 기억 추가
python cli/memory_cli.py stm "오늘은 날씨가 좋다"

# 단기 기억 조회
python cli/memory_cli.py get-stm

# 프롬프트 생성
python cli/memory_cli.py prompt -i "프로젝트 진행 상황이 어때?"
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
- GET `/api/v1/search?keywords=키워드1,키워드2` - 키워드로 검색
- GET, POST, DELETE `/api/v1/stm` - 단기 기억 관리
- POST `/api/v1/prompt` - 프롬프트 생성
- GET `/api/v1/verify` - 블록체인 무결성 검증

### Python 라이브러리

```python
from memory_engine import BlockManager, STMManager, CacheManager, PromptWrapper
from memory_engine.text_utils import process_user_input

# 사용자 입력 처리
user_input = "새 프로젝트를 시작했는데 너무 재미있다"
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

# 프롬프트 생성
cache_manager = CacheManager(block_manager=block_manager)
prompt_wrapper = PromptWrapper(cache_manager=cache_manager)

user_question = "프로젝트 진행 상황이 어때?"
prompt = prompt_wrapper.compose_prompt(user_question)

# LLM에 전달
# llm_response = call_your_llm(prompt)
```

## 🧱 아키텍처

```
memory-block-engine/
├── memory_engine/    # 핵심 라이브러리
│   ├── block_manager.py    # 장기 기억 관리
│   ├── stm_manager.py      # 단기 기억 관리
│   ├── cache_manager.py    # 웨이포인트 캐시
│   ├── prompt_wrapper.py   # 프롬프트 조합
│   ├── text_utils.py       # 텍스트 처리 유틸리티
├── api/              # REST API 인터페이스
├── cli/              # 커맨드라인 도구
├── data/             # 데이터 저장 디렉토리
```

## 📊 기억 블록 구조

```json
{
  "block_index": 143,
  "timestamp": "2025-05-08T01:02:33",
  "context": "새 프로젝트를 시작했는데 너무 재미있다",
  "keywords": ["프로젝트", "시작", "재미"],
  "tags": ["긍정적", "시작", "의욕"],
  "embedding": [0.131, 0.847, ...],
  "importance": 0.91,
  "hash": "...",
  "prev_hash": "..."
}
```

## 🔧 프로젝트 확장

- **임베딩 개선**: 실제 임베딩 모델(예: sentence-transformers) 통합
- **키워드 추출 개선**: 한국어 형태소 분석기 기반 키워드 추출 구현
- **클라우드 연동**: 데이터베이스 백엔드 추가 (SQLite, MongoDB 등)
- **분산 처리**: 대규모 기억 관리를 위한 분산 처리 구현

## 📄 라이센스

MIT License

## 👥 기여

버그 리포트, 기능 제안, 풀 리퀘스트 등 모든 기여를 환영합니다!

## 📱 연락처

이메일: example@email.com 
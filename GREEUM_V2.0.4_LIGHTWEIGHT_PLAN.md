# Greeum v2.0.4 경량화 계획서

**목표**: Optional dependencies 제거를 통한 패키지 경량화 및 안정성 향상

## 📊 현황 분석 (2025-07-30)

### ✅ 완료된 작업들 (v2.0.1 → v2.0.3)
1. **MCP 서버 하드코딩 경로 제거** - 크로스 환경 호환성 확보
2. **MCP 모듈 의존성 오류 해결** - pyproject.toml에 `mcp>=1.0.0` 추가
3. **MCP 서버 API 수정** - BlockManager 직접 사용 대신 CLI 패턴 구현
4. **v2.0.3 배포 완료** - PyPI에 API 수정사항 포함하여 배포

### 🔍 의존성 분석 결과
#### 현재 실제 사용 패턴:
- **CLI**: `greeum memory add/search` → SimpleEmbedding (128차원)
- **MCP 서버**: `add_memory/search_memory` → SimpleEmbedding 
- **기본 등록 모델**: `['simple']`만 존재
- **핵심 워크플로우**: 모든 기능이 SimpleEmbedding 기반으로 동작

#### 거의 사용되지 않는 고급 기능들:
- **OpenAI**: CLI에서 `--openai-key` 옵션조차 제공 안함
- **FAISS**: 문서에만 존재, 실제 핵심 워크플로우에서 사용 안함
- **SentenceTransformers**: 수동 설정 필요, 복잡한 초기화 과정

## 🎯 v2.0.4 경량화 목표

### 제거 대상 (Optional Dependencies)
```toml
# 현재 pyproject.toml에서 제거할 섹션들
[project.optional-dependencies]
api = ["fastapi>=0.100.0", "uvicorn>=0.15.0"]
search = ["faiss-cpu>=1.7.0", "transformers>=4.20.0"]
ai = ["openai>=1.0.0", "anthropic>=0.3.0"]
all = ["greeum[api,search,ai]"]

# Legacy compatibility (v1.0 style) - 전체 제거
faiss = ["faiss-cpu>=1.7.4"]
openai = ["openai>=1.0.0"]
transformers = ["transformers>=4.40.0", "sentence-transformers>=2.2.0", "keybert>=0.7.0"]
```

### 코드 제거 대상

#### 1. `greeum/embedding_models.py`
```python
# 제거할 클래스들
class OpenAIEmbedding(EmbeddingModel):     # 전체 제거
class SentenceTransformerEmbedding(EmbeddingModel):  # 전체 제거

# 제거할 함수들
def init_sentence_transformer(...):        # 전체 제거
def init_openai(...):                      # 전체 제거
```

#### 2. `greeum/core/vector_index.py`
```python
# 파일 전체 제거 또는 클래스 제거
class FaissVectorIndex:                    # 전체 제거
```

#### 3. `greeum/core/block_manager.py`
```python
# FAISS 관련 코드 섹션들 제거
try:
    import faiss  # type: ignore
    # ... FAISS 관련 코드
except Exception:
    # fallback 코드는 유지
```

#### 4. `greeum/__init__.py`
```python
# 제거할 import들
from .embedding_models import (
    # SimpleEmbeddingModel만 유지
    SentenceTransformerEmbedding,  # 제거
    OpenAIEmbedding,              # 제거
    init_sentence_transformer,    # 제거
    init_openai                   # 제거
)

# __all__에서 제거
"SentenceTransformerEmbedding",  # 제거
"OpenAIEmbedding",              # 제거
"init_sentence_transformer",    # 제거
"init_openai",                  # 제거
```

### 유지할 핵심 기능들 (100% 보장)
- ✅ CLI `greeum memory add/search` 명령어
- ✅ MCP 서버 `add_memory/search_memory` 도구
- ✅ SimpleEmbedding 기반 검색 (128차원 hash-based)
- ✅ SQLite 데이터베이스 저장
- ✅ 키워드 검색 기능
- ✅ 모든 STM/LTM 기본 기능
- ✅ JSON-RPC MCP 프로토콜 지원
- ✅ Claude Code 연동

## 📈 예상 효과

### 🎯 성능 개선
- **패키지 크기**: ~500MB → ~50MB (90% 감소)
- **설치 시간**: ~5분 → ~30초 (10배 향상)
- **의존성 충돌**: 거의 제로
- **ARM Mac 호환성**: 완벽 지원

### 🛡️ 안정성 향상
- **의존성 수**: 12개 → 6개 (50% 감소)
- **ML 라이브러리 의존성**: 완전 제거
- **버전 충돌 위험**: 대폭 감소
- **크로스 플랫폼 지원**: 향상

### 🚀 배포 이점
- **pipx 설치**: 더 빠르고 안정적
- **Docker 이미지**: 크기 대폭 감소
- **CI/CD**: 빌드 시간 단축
- **유지보수**: 복잡성 80% 감소

## 🗓️ 작업 일정

### Phase 1: 코드 정리 (1-2시간)
1. pyproject.toml optional-dependencies 섹션 제거
2. embedding_models.py에서 고급 클래스들 제거
3. vector_index.py 파일 제거 또는 정리
4. __init__.py import 정리
5. 관련 문서 업데이트

### Phase 2: 테스트 (30분)
1. 로컬 CLI 기능 테스트
2. MCP 서버 기능 테스트  
3. 핵심 워크플로우 검증

### Phase 3: 배포 (30분)
1. v2.0.4 빌드
2. PyPI 배포
3. 다른 환경에서 설치 테스트

## ⚠️ 호환성 고려사항

### Breaking Changes
- `OpenAIEmbedding`, `SentenceTransformerEmbedding` 클래스 제거
- `FaissVectorIndex` 클래스 제거
- Optional dependencies 제거

### Migration Path (필요한 경우)
고급 기능이 정말 필요한 1% 사용자를 위해:
```bash
# 별도 확장 패키지 제안 (미래 고려사항)
pip install greeum-extensions  # OpenAI, FAISS 등 포함
```

## 📋 최종 패키지 구성 (v2.0.4)

### 필수 의존성 (6개)
```toml
dependencies = [
    "rich>=13.4.0",      # CLI 출력
    "click>=8.1.0",      # CLI 명령어
    "numpy>=1.24.0",     # 수치 연산
    "sqlalchemy>=2.0.0", # 데이터베이스
    "pydantic>=2.0.0",   # 데이터 검증
    "mcp>=1.0.0",        # MCP 프로토콜
]
```

### 핵심 모듈 구성
```
greeum/
├── __init__.py           # 필수 export만
├── cli.py                # CLI 인터페이스
├── client.py             # API 클라이언트
├── text_utils.py         # 텍스트 처리
├── embedding_models.py   # SimpleEmbedding만
├── core/
│   ├── database_manager.py
│   ├── block_manager.py  # FAISS 코드 제거
│   ├── stm_manager.py
│   └── prompt_wrapper.py
└── mcp/
    ├── claude_code_mcp_server.py
    └── cli.py
```

## 🎉 성공 지표

### 기술적 지표
- [ ] 패키지 크기 50MB 이하
- [ ] 설치 시간 1분 이하
- [ ] 의존성 6개 이하
- [ ] 모든 핵심 기능 정상 동작

### 사용성 지표  
- [ ] `pipx install greeum` 30초 이내 완료
- [ ] Claude Code MCP 연결 즉시 성공
- [ ] 다른 환경에서 설치 문제 제로

---

**결론**: Greeum v2.0.4는 "핵심 기능 100% + 복잡성 80% 감소"를 달성하는 경량화 버전이 될 것입니다.
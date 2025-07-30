# Greeum v2.0 마이그레이션 상세 설계서

## 📋 프로젝트 개요

**목표**: Greeum과 GreeumMCP를 단일 패키지로 통합하여 사용자 편의성 극대화

**현재 상태**:
- Greeum v1.0.0: 핵심 메모리 엔진 안정화 완료
- GreeumMCP v1.0.0: MCP 서버 별도 패키지로 운영
- 문제점: 이중 설치, 복잡한 설정, 문서 분산

**목표 상태**:
- Greeum v2.0.0: 단일 패키지 + extras 기반 확장
- 명령어 간소화: `pip install greeum[mcp]` → `greeum mcp serve`
- 사용자 경험 획기적 개선

## 🏗️ 아키텍처 설계

### 현재 구조 (v1.0.0)
```
Greeum/
├── greeum/
│   ├── __init__.py
│   ├── block_manager.py      # LTM (블록체인 유사)
│   ├── stm_manager.py        # STM (DB 기반)
│   ├── cache_manager.py      # 웨이포인트 캐시
│   ├── prompt_wrapper.py     # 프롬프트 조합
│   ├── search_engine.py      # 다층 검색
│   └── ...

GreeumMCP/
├── greeummcp/
│   ├── __init__.py
│   ├── server.py             # MCP 서버
│   └── handlers.py           # MCP 핸들러
```

### 목표 구조 (v2.0.0)
```
greeum/
├── greeum/
│   ├── __init__.py              # 통합 API 노출
│   ├── core/                    # 기존 메모리 엔진 (강화)
│   │   ├── __init__.py
│   │   ├── block_manager.py     # LTM + 특화 도구
│   │   ├── stm_manager.py       # STM + 특화 도구
│   │   ├── cache_manager.py
│   │   ├── prompt_wrapper.py
│   │   ├── search_engine.py
│   │   └── ...
│   ├── cli/                     # 통합 CLI 시스템
│   │   ├── __init__.py          # 메인 greeum 명령어
│   │   ├── memory.py            # memory 서브명령어
│   │   ├── mcp.py               # mcp 서브명령어
│   │   └── api.py               # api 서브명령어
│   ├── mcp/                     # GreeumMCP 마이그레이션
│   │   ├── __init__.py
│   │   ├── server.py            # MCP 서버 (이전)
│   │   └── handlers.py          # MCP 핸들러 (이전)
│   └── api/                     # 기존 API 유지
│       └── memory_api.py
├── pyproject.toml               # extras 통합 설정
├── README.md                    # 단일 문서
└── MIGRATION_GUIDE.md           # 기존 사용자용 가이드
```

## 🎯 핵심 기능 강화

### STM (단기 기억) 특화 도구
```python
# greeum/core/stm_manager.py 확장
class STMManager:
    def promote_to_ltm(self, threshold=0.8):
        """중요한 STM → LTM 자동 승격"""
        
    def auto_cleanup_smart(self):
        """지능형 STM 정리 (중요도 기반)"""
        
    def get_context_relevant(self, query):
        """현재 맥락 관련 STM 필터링"""
        
    def export_session_summary(self):
        """STM 세션을 LTM 요약으로 변환"""
```

### LTM (장기 기억) 특화 도구
```python
# greeum/core/block_manager.py 확장
class BlockManager:
    def analyze_trends(self, timeframe="6months"):
        """장기 패턴 분석 (감정, 주제, 빈도)"""
        
    def verify_chain_integrity(self):
        """블록체인 무결성 검증"""
        
    def search_semantic_deep(self, query, max_depth=5):
        """의미적 연관성 깊이 탐색"""
        
    def export_blockchain_format(self):
        """블록 구조 그대로 내보내기"""
```

## 📝 CLI 명령어 체계

### 현재 (v1.0.0)
```bash
# 복잡한 경로 기반 실행
python cli/memory_cli.py add -c "내용"
python cli/memory_cli.py search -k "키워드"

# 별도 패키지 MCP
pip install greeummcp
python3 /path/to/minimal_mcp_server.py
```

### 목표 (v2.0.0)
```bash
# 통합 CLI
greeum memory add "내용"
greeum memory search "키워드"
greeum memory smart-search "맥락 검색"

# STM 전용
greeum stm add "임시 메모" --ttl 1h
greeum stm promote --threshold 0.8
greeum stm cleanup --smart

# LTM 전용  
greeum ltm analyze --trends --period 6m
greeum ltm verify --integrity
greeum ltm export --format blockchain

# MCP 서버 (한 줄!)
greeum mcp serve --transport stdio

# API 서버
greeum api serve --port 5000
```

## ⚙️ pyproject.toml 설계

```toml
[project]
name = "greeum"
version = "2.0.0"
description = "Universal memory module for LLMs with STM/LTM architecture"
authors = [{name = "Greeum Team", email = "contact@greeum.dev"}]
license = {text = "MIT"}
readme = "README.md"
requires-python = ">=3.10"

dependencies = [
    "click>=8.1.0",           # CLI 프레임워크
    "rich>=13.4.0",           # 터미널 UI
    "numpy>=1.24.0",          # 벡터 연산
    "sqlalchemy>=2.0.0",      # DB 추상화
    "pydantic>=2.0.0",        # 데이터 검증
]

[project.optional-dependencies]
mcp = [
    "mcp>=1.0.0",             # MCP 프로토콜
]
api = [
    "fastapi>=0.100.0",       # REST API
    "uvicorn>=0.15.0",        # ASGI 서버
]
search = [
    "faiss-cpu>=1.7.0",       # 벡터 검색
    "transformers>=4.20.0",   # BERT 임베딩
]
ai = [
    "openai>=1.0.0",          # OpenAI API
    "anthropic>=0.3.0",       # Claude API
]
all = [
    "greeum[mcp,api,search,ai]"
]

[project.scripts]
greeum = "greeum.cli:main"

[project.urls]
Homepage = "https://github.com/DryRainEnt/Greeum"
Documentation = "https://greeum.readthedocs.io"
Repository = "https://github.com/DryRainEnt/Greeum"
Issues = "https://github.com/DryRainEnt/Greeum/issues"
```

## 🔄 마이그레이션 단계별 계획

### Phase 1: 구조 준비 (30분)
1. **디렉토리 생성**
   ```bash
   mkdir -p greeum/core greeum/cli greeum/mcp
   ```

2. **기존 파일 이동**
   ```bash
   # 핵심 모듈을 core로 이동
   mv greeum/*.py greeum/core/ (select files)
   ```

3. **__init__.py 갱신**
   - 기존 import 경로 호환성 유지
   - 새로운 API 노출

### Phase 2: GreeumMCP 통합 (45분)
1. **파일 복사**
   ```bash
   cp -r ../GreeumMCP/greeummcp/* greeum/mcp/
   ```

2. **import 경로 수정**
   ```python
   # Before
   import greeummcp.server
   
   # After  
   import greeum.mcp.server
   ```

3. **의존성 충돌 해결**
   - 중복 의존성 제거
   - 버전 호환성 확인

### Phase 3: CLI 통합 (30분)
1. **Click 기반 명령어 구조**
   ```python
   @click.group()
   def main():
       """Greeum Universal Memory System"""
       
   @main.group()
   def memory():
       """Memory management commands"""
       
   @main.group()
   def mcp():
       """MCP server commands"""
   ```

2. **기존 CLI 이전**
   - 현재 cli/memory_cli.py 기능 통합
   - 새로운 명령어 체계 적용

### Phase 4: 검증 및 테스트 (20분)
1. **기능 테스트**
   ```bash
   greeum memory add "테스트 메모리"
   greeum memory search "테스트"
   greeum mcp serve --test
   ```

2. **호환성 테스트**
   ```python
   # 기존 코드가 여전히 동작하는지 확인
   from greeum import BlockManager, STMManager
   ```

### Phase 5: 문서화 (15분)
1. **README.md 통합**
2. **MIGRATION_GUIDE.md 생성**
3. **API 문서 갱신**

## 🛡️ 안전장치 및 롤백 계획

### 백업 전략
- **git tag v1.0.0-backup**: 마이그레이션 전 상태 태깅
- **브랜치 보호**: main 브랜치 푸시 전 충분한 테스트
- **GreeumMCP 보존**: 원본 레포지토리 유지 (deprecated 표시)

### 롤백 시나리오
1. **즉시 롤백 필요시**: `git reset --hard v1.0.0-backup`
2. **부분 롤백 필요시**: 특정 파일만 이전 버전으로 복구
3. **의존성 문제시**: pyproject.toml 단계별 롤백

### 검증 체크리스트
- [ ] 기존 Python import 경로 정상 작동
- [ ] CLI 명령어 모두 정상 실행
- [ ] MCP 서버 연결 정상
- [ ] API 서버 정상 실행
- [ ] 메모리 저장/검색 기능 정상
- [ ] 벤치마크 성능 유지 (±5% 이내)

## 🚨 위험 요소 및 대응책

### 높은 위험
1. **import 경로 변경으로 인한 기존 코드 파손**
   - 대응: __init__.py에서 하위 호환성 유지
   - 검증: 기존 예제 코드 전체 테스트

2. **의존성 충돌**
   - 대응: requirements.txt 세밀한 버전 관리
   - 검증: 가상환경에서 clean install 테스트

### 중간 위험
1. **MCP 서버 프로토콜 호환성**
   - 대응: 기존 minimal_mcp_server.py 병행 유지
   - 검증: Claude Desktop 연결 테스트

2. **성능 저하**
   - 대응: 벤치마크 스크립트로 사전/사후 비교
   - 검증: 중요 API 응답시간 측정

## 📊 성공 지표

### 사용자 경험 개선
- **설치 명령어**: 2개 → 1개 (50% 감소)
- **MCP 설정**: 5단계 → 2단계 (60% 감소)
- **문서 분산**: 2개 레포 → 1개 레포 (통합)

### 기술적 지표
- **패키지 크기**: 현재 대비 ±10% 이내
- **import 시간**: 현재 대비 ±5% 이내  
- **메모리 사용량**: 현재 대비 ±10% 이내

## 🎯 맥락 유실 방지 전략

### 진행 상황 문서화
- 각 Phase 완료 시 이 문서에 체크마크 및 결과 기록
- 문제 발생 시 즉시 ISSUES 섹션에 기록
- 중요 결정사항은 DECISIONS 섹션에 기록

### 메모리 외부화
- 진행 상황을 Greeum MCP 메모리에 실시간 저장
- 주요 코드 변경사항을 git commit으로 세분화
- 각 단계별 작동 스크린샷 보존

## 📅 진행 상황 추적

### Phase 1: 구조 준비
- [ ] 시작 시간: 
- [ ] 디렉토리 생성 완료
- [ ] 파일 이동 완료
- [ ] __init__.py 갱신 완료
- [ ] 완료 시간:
- [ ] 검증 결과:

### Phase 2: GreeumMCP 통합  
- [ ] 시작 시간:
- [ ] 파일 복사 완료
- [ ] import 경로 수정 완료
- [ ] 의존성 충돌 해결 완료
- [ ] 완료 시간:
- [ ] 검증 결과:

### Phase 3: CLI 통합
- [ ] 시작 시간:
- [ ] Click 구조 구현 완료
- [ ] 기존 CLI 이전 완료
- [ ] 완료 시간:
- [ ] 검증 결과:

### Phase 4: 검증 및 테스트
- [ ] 시작 시간:
- [ ] 기능 테스트 완료
- [ ] 호환성 테스트 완료
- [ ] 완료 시간:
- [ ] 검증 결과:

### Phase 5: 문서화
- [ ] 시작 시간:
- [ ] README.md 통합 완료
- [ ] MIGRATION_GUIDE.md 생성 완료
- [ ] API 문서 갱신 완료
- [ ] 완료 시간:
- [ ] 검증 결과:

## 📝 중요 결정사항 기록
- 

## ⚠️ 발생한 문제들
- 

## ✅ 최종 검증 체크리스트
- [ ] 기존 Python import 경로 정상 작동
- [ ] CLI 명령어 모두 정상 실행  
- [ ] MCP 서버 연결 정상
- [ ] API 서버 정상 실행
- [ ] 메모리 저장/검색 기능 정상
- [ ] 벤치마크 성능 유지
- [ ] 문서 갱신 완료
- [ ] PyPI 배포 준비 완료

---

**이 문서는 Greeum v2.0 마이그레이션의 완전한 가이드이며, 맥락 유실 방지와 안전한 진행을 위한 모든 정보를 포함합니다.**
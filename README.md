# 🧠 Greeum v2.0.5

<p align="center">
  <a href="README.md">🇰🇷 한국어</a> |
  <a href="docs/i18n/README_EN.md">🇺🇸 English</a> |
  <a href="docs/i18n/README_JP.md">🇯🇵 日本語</a> |
  <a href="docs/i18n/README_ZH.md">🇨🇳 中文</a>
</p>

LLM을 위한 지능적 기억 관리 시스템

## 📌 개요

**Greeum** (발음: 그리움)은 모든 LLM(대규모 언어 모델)에 연결할 수 있는 **범용 기억 모듈**입니다:

- **장기 기억**: 사용자 맥락, 선호도, 목표를 영구 저장
- **단기 기억**: 대화 세션 내 중요 정보 관리  
- **지능적 검색**: 맥락 기반 자동 기억 회상
- **품질 관리**: 메모리 품질 자동 검증 및 최적화
- **다국어 지원**: 한국어, 영어, 일본어, 중국어 완벽 지원

이름 "Greeum"은 한국어 "그리움"에서 영감을 받았으며, AI가 과거를 기억하고 그리워하는 능력을 상징합니다.

## 🚀 빠른 시작

### 설치

```bash
# pipx로 설치 (권장)
pipx install greeum

# 또는 pip로 설치
pip install greeum
```

### 기본 사용법

```bash
# 기억 추가
python3 -m greeum.cli memory add "오늘 새로운 프로젝트를 시작했다. Python으로 웹 애플리케이션을 개발할 예정이다."

# 기억 검색
python3 -m greeum.cli memory search "프로젝트 Python" --limit 5

# 장기 기억 분석
python3 -m greeum.cli ltm analyze --period 30d --trends

# 단기 기억 추가
python3 -m greeum.cli stm add "임시 메모" --ttl 1h

# MCP 서버 실행
python3 -m greeum.mcp.claude_code_mcp_server
```

## 🔑 주요 기능

### 📚 다층 메모리 시스템
- **LTM (장기 기억)**: 블록체인 유사 구조로 영구 저장
- **STM (단기 기억)**: TTL 기반 임시 메모리 관리
- **웨이포인트 캐시**: 현재 맥락 관련 기억 자동 로딩

### 🧠 지능적 기억 관리
- **품질 검증**: 7개 지표 기반 자동 품질 평가
- **중복 탐지**: 85% 유사도 기준 중복 방지
- **사용 분석**: 패턴 분석 및 최적화 권장
- **자동 정리**: 품질 기반 메모리 정리

### 🔍 고급 검색
- **키워드 검색**: 태그 및 키워드 기반
- **벡터 검색**: 의미적 유사도 검색
- **시간 검색**: "3일 전", "지난 주" 등 자연어 시간 표현
- **하이브리드 검색**: 키워드 + 벡터 + 시간 조합

### 🌐 MCP 통합
- **Claude Code**: 12개 MCP 도구로 완벽 통합
- **실시간 동기화**: 메모리 생성/검색 실시간 반영
- **품질 검증**: 자동 품질 체크 및 피드백

## 🛠️ 고급 사용법

### API 사용
```python
from greeum import BlockManager, STMManager, PromptWrapper

# 메모리 시스템 초기화
bm = BlockManager()
stm = STMManager()
pw = PromptWrapper()

# 기억 추가
bm.add_block(
    context="중요한 회의 내용",
    keywords=["회의", "결정사항"],
    importance=0.9
)

# 컨텍스트 기반 프롬프트 생성
enhanced_prompt = pw.compose_prompt("지난 회의에서 뭘 결정했지?")
```

### MCP 도구 (Claude Code용)
```
Available tools:
- add_memory: 새 기억 추가
- search_memory: 기억 검색  
- get_memory_stats: 메모리 통계
- ltm_analyze: 장기 기억 분석
- stm_add: 단기 기억 추가
- quality_check: 품질 검증
- check_duplicates: 중복 확인
- usage_analytics: 사용 분석
- ltm_verify: 무결성 검증
- ltm_export: 데이터 내보내기
- stm_promote: STM→LTM 승격
- stm_cleanup: STM 정리
```

## 📊 메모리 품질 관리

Greeum v2.0.5는 지능적 품질 관리 시스템을 제공합니다:

### 품질 평가 지표
1. **길이**: 적절한 정보량
2. **풍부도**: 의미있는 단어 비율
3. **구조**: 문장/단락 구성도
4. **언어**: 문법 및 표현 품질
5. **정보 밀도**: 구체적 정보 포함도
6. **검색성**: 향후 검색 용이성
7. **시간적 관련성**: 현재 맥락 연관성

### 자동 최적화
- **품질 기반 중요도 조정**
- **중복 메모리 자동 탐지**
- **STM→LTM 승격 제안**
- **사용 패턴 기반 권장사항**

## 🔗 연동 가이드

### Claude Code MCP 설정
1. **설치 확인**
   ```bash
   greeum --version  # v2.0.5 이상
   ```

2. **Claude Desktop 설정**
   ```json
   {
     "mcpServers": {
       "greeum": {
         "command": "python3",
         "args": ["/path/to/greeum/mcp/claude_code_mcp_server.py"],
         "env": {
           "GREEUM_DATA_DIR": "/path/to/data"
         }
       }
     }
   }
   ```

3. **연결 확인**
   ```bash
   claude mcp list  # greeum 서버 확인
   ```

### 다른 LLM 연동
```python
# OpenAI GPT
from greeum.client import MemoryClient
client = MemoryClient(llm_type="openai")

# 로컬 LLM
client = MemoryClient(llm_type="local", endpoint="http://localhost:8080")
```

## 📈 성능 및 벤치마크

- **응답 품질**: 평균 18.6% 향상 (벤치마크 기준)
- **검색 속도**: 5.04배 향상 (웨이포인트 캐시 적용)
- **재질문 감소**: 78.2% 감소 (맥락 이해도 향상)
- **메모리 효율**: 메모리 사용량 50% 최적화

## 📚 문서 및 리소스

- **[시작하기](docs/get-started.md)**: 상세 설치 및 설정 가이드
- **[API 문서](docs/api-reference.md)**: 전체 API 레퍼런스
- **[튜토리얼](docs/tutorials.md)**: 단계별 사용 예제
- **[개발자 가이드](docs/developer_guide.md)**: 개발 참여 방법

## 🤝 기여하기

Greeum은 오픈소스 프로젝트입니다. 기여를 환영합니다!

### 기여 방법
1. **이슈 리포트**: 버그나 문제점을 발견하신 경우
2. **기능 제안**: 새로운 아이디어나 개선사항
3. **코드 기여**: Pull Request 환영
4. **문서 개선**: 문서 번역 및 개선

### 개발 환경 구성
```bash
# 소스 코드 다운로드 후
pip install -e .[dev]
tox  # 테스트 실행
```

## 📞 지원 및 연락처

- **📧 공식 이메일**: playtart@play-t.art
- **🌐 공식 웹사이트**: [greeum.app](https://greeum.app)
- **📚 문서**: 이 README 및 docs/ 폴더 참조

## 📄 라이센스

이 프로젝트는 MIT 라이센스 하에 배포됩니다. 자세한 내용은 [LICENSE](LICENSE) 파일을 참조하세요.

## 🏆 인정사항

- **OpenAI**: 임베딩 API 지원
- **Anthropic**: Claude MCP 플랫폼
- **NumPy**: 효율적인 벡터 계산
- **SQLite**: 안정적인 데이터 저장

---

<p align="center">
  Made with ❤️ by the Greeum Team<br>
  <em>"AI가 기억을 통해 더 인간적이 되기를"</em>
</p>
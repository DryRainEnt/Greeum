# Greeum 소개 (한국어)

> 대화형 AI가 장기 기억을 유지하도록 돕는 로컬 메모리 시스템입니다.

## 1. 설치 및 초기 설정

```bash
pipx install --pip-args "--pre" greeum  # 권장 방식
# 또는
pip install --upgrade "greeum"

# 데이터 디렉터리 생성 및 기본 설정
greeum setup
```

### (선택) 의미 임베딩 활성화
```bash
pip install sentence-transformers
greeum mcp warmup  # 모델 캐시 미리 다운로드
```
- 기본값은 해시 기반 폴백(SimpleEmbedding)입니다.
- 의미 기반 검색이 필요하면 다음과 같이 실행하세요.
  ```bash
  greeum mcp serve --semantic
  ```

## 2. MCP 연동 요약

| 환경 | 실행 명령 | 비고 |
|------|-----------|------|
| Codex (STDIO) | `greeum mcp serve -t stdio` | 설정 파일에서 `GREEUM_QUIET=true` 권장 |
| ClaudeCode / Cursor | `greeum mcp serve` | `--semantic` 옵션으로 의미 검색 활성화 |
| HTTP (ChatGPT 등) | `greeum mcp serve -t http --host 0.0.0.0 --port 8800` | 엔드포인트: `http://127.0.0.1:8800/mcp` |

> **팁**: `greeum setup`을 실행한 뒤 MCP 연결을 시도하면 초기 타임아웃을 피할 수 있습니다.

## 3. 권장 프롬프트 규칙
- 작업 시작 전에 `search_memory`로 기존 결정/요약을 확인합니다.
- 작업 종료 시 `add_memory` 도구로 요약을 남깁니다.
- 자주 참조하는 주제는 앵커 슬롯(A/B/C)에 고정하여 빠르게 검색합니다.

## 4. 주요 CLI 명령
```bash
# 메모리 추가
greeum memory add "이번 스프린트 주요 이슈 정리"

# 검색
greeum memory search "스프린트 이슈" --count 5

# 브랜치 인덱스 재구축
greeum memory reindex --disable-faiss  # 키워드 전용
```

## 5. 추가 문서
- [설치 가이드](get-started.md)
- [MCP 통합 문서](mcp-integration.md)
- [워크플로 자동화](greeum-workflow-guide.md)
- [API 레퍼런스](api-reference.md)

---

© 2025 Greeum Contributors — MIT License

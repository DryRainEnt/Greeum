# Greeum Roadmap — Harness Integration

**작성**: 2026-05-30
**상태**: 방향 합의 단계 (이슈는 `docs/issues/` 참조)

## 비전

Greeum을 **여러 기성 하네스(코딩 에이전트·LLM 프론트엔드)에 꽂히는 RAG/메모리 레이어**로 만든다.
독립 도구가 아니라, 사용자가 이미 쓰는 하네스에 메모리 기능을 주입하는 미들웨어.

## 현재 위치 (~70%)

2026년 기준 MCP가 사실상 모든 하네스의 공용 연동 표준이 됐고, Greeum은 이미 핵심 표면을 갖춤:

| 표면 | 상태 | 비고 |
|------|------|------|
| MCP (stdio) | ✅ 작동 | `greeum mcp serve`, `greeum/mcp/native/` |
| MCP (HTTP) | ⚠️ 부분 | `native/http_server.py` — 비스펙·무인증 (이슈 참조) |
| REST API | ✅ 작동 | FastAPI :8400, X-API-Key |
| Python SDK | ✅ 작동 | `from greeum import ...` |
| CLI | ✅ 작동 | 5개 진입점 |
| LangChain/LlamaIndex 어댑터 | ❌ 없음 | |
| Anthropic memory-tool 심 | ❌ 없음 | |

경쟁자(mem0·Zep·Letta·Supermemory)도 동일하게 MCP+REST+SDK 3종을 제공.
Supermemory가 "코딩 에이전트용 메모리 MCP"로 가장 근접한 경쟁자.

## 우선순위 (레버리지 순)

1. **[P0] MCP-over-HTTP 스펙 준수 + 인증** — Streamable HTTP + OAuth/API-key.
   원격/호스팅, OpenAI Responses, Claude Connectors, Open WebUI 등이 열림.
   → `docs/issues/2026-05-30-mcp-http-transport-spec-auth.md`
2. **[P0] 임베딩 패키징 전략** — "작게 vs 성능"의 반복 난제 해결. 드롭인 신뢰성의 핵심.
   → `docs/issues/2026-05-30-embedding-packaging-strategy.md`
3. **[P1] LangChain `BaseRetriever` + LlamaIndex retriever 어댑터** — RAG 빌더 생태계 진입.
   → `docs/issues/2026-05-30-langchain-llamaindex-adapters.md`
4. **[P1] Anthropic 네이티브 memory-tool(`memory_20250818`) 심** — Claude 생태계, Supermemory 정면 경쟁.
   → `docs/issues/2026-05-30-anthropic-memory-tool-shim.md`
5. **[P2] MCP 구현 정리** — `native/`(정본) vs 레거시 삼중 중복 제거.
   → `docs/issues/2026-05-30-mcp-implementation-consolidation.md`
6. **[P2] 하네스별 설정 문서 + 원클릭 딥링크** — 채택 마찰 제거 (문서/UX, 코드 적음).

## 차별점 (표면이 같으니 내용으로)

- 브랜치/그래프 구조 (anchor·DFS·association)
- actant(그레마스) 라벨링 모델
- 로컬-퍼스트 + Tailscale 원격 주입 (이미 작동)
- 다국어/한국어 1급 지원

## 핵심 리스크

**임베딩 풋건**: sentence-transformers 미설치 시 해시 폴백으로 RAG가 조용히 무력화.
게다가 `greeum mcp serve`는 기본값이 `GREEUM_DISABLE_ST=1`. "아무 하네스에나 꽂으면 된다"는 약속과 정면 충돌. → 우선순위 2번에서 해결.

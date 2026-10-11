# Greeum 프로젝트 종료 (2026-10-11)

Greeum의 여정은 2026-10-11에 끝났다. 이 문서는 왜 멈췄는지, 어디까지 왔는지, 무엇이 남았는지를 기록한다.

## 종료 이유 (운영자의 말)

- 기획·설계 역량으로는 이 프로젝트가 장기적으로 유의미한 혁신을 만들 수 있다는 확신을 누구에게도 줄 수 없었다.
- 데이터 수집 과정에서 토큰 낭비가 심했다.
- 의도했던 "기억 간 연결망"은 결국 고전적인 신경망 학습의 하위호환에 머물렀다.

호기롭게 시작했지만 수평선 너머의 여명을 보지 못했고, 그 책임은 운영자 본인에게 있다는 것이 운영자의 결론이다.

## 마지막 상태

| 항목 | 상태 |
|------|------|
| 마지막 기능 커밋 | `b587b88` (2026-07-27) — 검색 시 query embedding이 항상 버려지던 침묵 버그 수정 |
| 기본 임베딩 | `intfloat/multilingual-e5-small` (ST) → Model2Vec → 시끄러운 hash 폴백 |
| 하이브리드 가중치 | vec 0.9 / bm25 0.1 (라이브 DB·MIRACL-Korean 양쪽 sweep 결과) |
| 라이브 배포 | 2026-08-10 v5.4 코드 + 임베딩 재마이그레이션(768-dim 통일), 서버 재기동 완료 |
| 평가 인프라 | `make eval-smoke`, NIAH 로그스케일, MIRACL-Korean (`docs/eval/`) |
| 어댑터 | LangChain, LlamaIndex, Anthropic memory-tool 심, MCP Streamable HTTP |

## 미해결 결함

- [`add_block` 무결성 — 유사 콘텐츠 유입 시 기존 블록 content가 변형되고 해시는 재계산되지 않음](issues/2026-10-11-add-block-silent-merge-integrity.md)
- [`ThreadSafeDatabaseManager`에 `get_recent_blocks` 누락 — MCP `get_recent_memories` 도구 오류](issues/2026-10-11-threadsafe-db-missing-get-recent-blocks.md)

## 남는 것

실측으로 얻은 결론들은 유효하다. hash 임베딩이 사실상 랜덤이었다는 발견, 평가가 우회하던 실제 검색 경로의 결함, 데이터 종류에 따라 뒤집히는 하이브리드 가중치. "추측 대신 실측으로 결정한다"는 원칙은 이 저장소 밖으로 가져갈 수 있다.

라이브 메모리 서버(`~/.greeum`, REST :8400)는 다른 프로젝트들이 계속 쓰는 인프라이므로, 이 저장소의 개발 종료와 서버 운용 중단은 별개의 결정이다.

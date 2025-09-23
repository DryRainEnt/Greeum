# Greeum 초간단 가이드

## 1. 설치 (Install)
```bash
pip install --pre greeum
# 또는 개발 환경에서
pip install -e .[dev]
```
- Python 3.10 이상을 권장합니다.
- `pipx install greeum`으로 전역 CLI 설치도 가능합니다.

## 2. 셋업 (Setup)
```bash
greeum setup --start-worker
```
- 데이터 디렉터리를 지정하면 CLI가 자동으로 만들고 저장합니다.
- `--start-worker`가 기본값입니다. 첫 실행에서 HTTP 워커를 띄우고 `/healthz`까지 확인합니다.
- SentenceTransformer를 쓰고 싶다면 `setup`에서 warmup을 실행하거나 `greeum mcp warmup --semantic`을 나중에 호출하세요.
- 요약 메시지에 워커 엔드포인트·로그 경로가 표시됩니다. 반복 실행 시 같은 워커를 재사용합니다.

## 3. 연동 (Integrate)
### CLI
```bash
greeum memory add "회의 요약" --importance 0.7
greeum memory search "회의" --count 5
```
- CLI는 항상 백그라운드 워커를 자동 감지합니다.
- 응답은 MCP와 동일한 서식으로 출력됩니다.

### Codex / Cursor / ChatGPT
1. `greeum setup`이 만든 워커 엔드포인트(기본 `http://127.0.0.1:8820/mcp`)를 확인합니다.
2. Codex CLI `mcp_config.json` 혹은 MCP STDIO 설정에 다음 항목을 추가합니다.
   ```json
   {
     "name": "greeum",
     "transport": "http",
     "endpoint": "http://127.0.0.1:8820/mcp",
     "command": []
   }
   ```
3. STDIO를 쓰는 도구(Claude Desktop 등)는 `greeum mcp serve -t stdio --semantic`을 그대로 지정하면 됩니다.

## 4. 룰 & 워크플로우 (Workfast Loop)
- **Search → Work → Add**: 작업 시작 시 `search_memory`, 마무리 시 `add_memory`로 한 줄 요약을 남기세요.
- **자동 로그 축적**: 백그라운드 워커가 `worker.log`를 기록하므로 이상 징후를 쉽게 추적할 수 있습니다.
- **중복 방지**: CLI/워커가 의미·해시 기반 중복 체크를 수행합니다. 경고가 뜨면 태그나 구체성을 보강하세요.

## 5. 자주 쓰는 명령
| 목적 | 명령 |
| --- | --- |
| 워커 상태 확인 | `curl http://127.0.0.1:8820/healthz` |
| 워커 로그 보기 | `tail -f ~/.greeum/worker.log` |
| 워커 재기동 | `greeum worker serve --host 127.0.0.1 --port 8820` |
| SentenceTransformer 재워밍 | `greeum mcp warmup --semantic` |

---
더 깊은 아키텍처와 체크리스트는 `docs/` 디렉터리의 세부 문서를 참고하세요. 최소한 위 세 단계만 완료하면 모든 MCP/CLI 환경에서 바로 기억을 저장하고 불러올 수 있습니다.

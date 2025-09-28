# Greeum

[![PyPI version](https://badge.fury.io/py/greeum.svg)](https://badge.fury.io/py/greeum)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

> 기억의 해방 — 지긋지긋한 컨텍스트 제한에서 자유로워지세요. Greeum은 MCP 호환 도구와 CLI가 동일한 장기 기억 저장소를 사용하도록 설계된 오픈소스 모듈입니다.

**왜 Greeum인가요?**
- 한 번의 설치와 셋업으로 Codex, ClaudeCode, Cursor, ChatGPT MCP에 등록할 수 있습니다.
- search → 작업 → add 루틴을 따라 저장된 기록을 슬롯(A/B/C)과 브랜치로 정리합니다.
- Branch 분석 리포트와 usage 통계 도구로 최근 활동과 슬롯 상태를 조회할 수 있습니다.
- 기본은 해시 기반 폴백 검색이며, SentenceTransformer를 설치하면 의미 검색을 추가로 사용할 수 있습니다.

<p align="center">
  <a href="README.md"><strong>English</strong></a> · <a href="docs/README_ko.md">한국어</a>
</p>

---

## 1. Installation & Setup

> **First run checklist**
> 1. Install the package (pipx or pip)
> 2. Run `greeum setup --start-worker` to create the data directory and launch the worker
> 3. Connect your MCP client (Codex, ClaudeCode, Cursor, …)

> ⚠️ **Platform support**: Greeum MCP는 Linux, macOS, WSL 환경에서 안정적으로 동작합니다. Windows PowerShell에서는 Codex STDIO 초기화가 반복적으로 실패할 수 있으므로 WSL을 사용하세요.

👉 **Need the ultra-short version?** See [`docs/QUICKSTART.md`](docs/QUICKSTART.md) for “설치 → 셋업 → 연동” 한 페이지 요약.

```bash
# Recommended (isolated) install
pipx install --pip-args "--pre" greeum

# or standard pip
pip install --upgrade "greeum"

# initialise data directory, choose where memories live
greeum setup --start-worker
```

### Optional: enable semantic embeddings
```bash
pip install sentence-transformers          # once per machine
greeum mcp warmup                          # downloads the default model
```
- MCP/CLI run with **hash fallback by default** for fast startup.
- Add `--semantic` (or unset `GREEUM_DISABLE_ST`) when you want the SentenceTransformer-enabled search:
  ```bash
  greeum mcp serve --semantic -t stdio
  ```

### Keep the worker running automatically
- **macOS**: create `~/Library/LaunchAgents/com.greeum.worker.plist` that runs `greeum worker serve --host 127.0.0.1 --port 8800 --semantic` at login.
- **Linux (systemd user)**: add a unit under `~/.config/systemd/user/greeum-worker.service` pointing to the same command and enable it with `systemctl --user enable --now greeum-worker`.
- **Windows**: register `greeum worker serve --host 127.0.0.1 --port 8800` in 작업 스케줄러 with the “로그온 시 실행” trigger.

---

## 2. MCP Integration

### Codex (STDIO)
1. Ensure `greeum setup` has been run at least once.
2. `~/.codex/config.toml`
   ```toml
   [mcp_servers.greeum]
   command = "greeum"
   args    = ["mcp", "serve", "-t", "stdio"]
   env     = { "GREEUM_QUIET" = "true", "PYTORCH_ENABLE_MPS_FALLBACK" = "1" }
   ```
3. Optional semantic mode:
   ```toml
   args = ["mcp", "serve", "-t", "stdio", "--semantic"]
   ```
   > First run may take longer while the model loads. Warm-up before enabling for smoother startup.

### ClaudeCode / Cursor (native MCP)
```bash
greeum mcp serve
```
- Add the command above to the client’s MCP configuration.
- Semantic mode: `greeum mcp serve --semantic`

### HTTP / URL-based MCP (e.g. ChatGPT)
```bash
greeum mcp serve -t http --host 0.0.0.0 --port 8800
```
Then register `http://127.0.0.1:8800/mcp` as the endpoint.

---

## 3. LLM Prompting Guidelines
- **Always close sessions with a summary**: “Call `add_memory` summarising decisions before ending the shift.”
- **Retrieve before writing**: run `search_memory` with the task keywords before starting work.
- **Use anchor slots (A/B/C)** for hot contexts:
  ```json
  {
    "name": "search_memory",
    "arguments": { "query": "login flow", "limit": 5, "slot": "A" }
  }
  ```
- Encourage agents to log important facts with `importance` ≥ 0.6 so team hand‑offs stay seamless.

---

## 4. CLI Essentials

```bash
# Add context
greeum memory add "Legal copy updated for release"

# Search (global fallback enabled by default)
greeum memory search "release notes" --count 5

# Anchor-based search (slot-aware)
greeum memory search "translations" --slot B --radius 2

# Rebuild branch indices (FAISS + keyword or keyword-only)
greeum memory reindex             # uses FAISS if available
greeum memory reindex --disable-faiss

# Reuse the long-running worker (avoids cold-start on each CLI call)
greeum worker serve --host 127.0.0.1 --port 8800   # terminal 1
export GREEUM_MCP_HTTP="http://127.0.0.1:8800/mcp" # terminal 2
greeum memory add "Sprint hand-off" --use-worker
greeum memory search "hand-off" --use-worker
```

Other useful commands:
- `greeum anchors status` / `set A <block>` / `pin A`
- `greeum workflow search "<topic>"` for scripted MCP calls
- `greeum mcp warmup` to cache the embedding model before enabling semantic mode

---

## 5. Documentation
- [Getting Started](docs/get-started.md)
- [MCP Integration Details](docs/mcp-integration.md)
- [Automation Workflow Guide](docs/greeum-workflow-guide.md)
- [API Reference](docs/api-reference.md)

---

## 6. License
MIT License — see [LICENSE](LICENSE).

---

**Greeum** · Persistent memory for AI—built and maintained by the community.

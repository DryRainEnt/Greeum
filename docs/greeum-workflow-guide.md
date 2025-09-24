# Greeum Workflow & Reminder Guide

Turn the `search → work → add` loop into a daily habit. Everything below uses the built-in commands that ship with `greeum==3.1.1rc4.dev1+`.

**First-time checklist**
- `pipx install --pip-args "--pre" greeum`
- `greeum setup` → choose the data directory, generate base schema, and optionally warm up semantic embeddings
- Update your MCP configuration to call `greeum mcp serve -t stdio` (instructions below)

## 1. Daily Flow (human-friendly)

1. **Pull context** – `greeum-workflow search "<topic>"` before you start. You get the most relevant memories instantly.
2. **Do the work** – keep Codex/IDE open; capture observations as you go.
3. **Finish with a summary** – `greeum-workflow add 0.6 "<summary>"` when you’re done (include decisions, blockers, dates).
4. **Weekly reflection** – run `greeum-digest` (or schedule it) to see what the team has saved.

## 2. Automation Building Blocks

### Workflow helper

```
greeum-workflow search "deployment checklist"
greeum-workflow add 0.55 "[CodexExperience-2025-09-19] Codex STDIO integration validated."
greeum-workflow recap --limit 10
greeum-workflow stats
```

- Override the CLI path when needed: `GREEUM_CLI_BIN=/path/to/greeum`.
- Quiet + Apple Silicon friendly: export `GREEUM_QUIET=true` and `PYTORCH_ENABLE_MPS_FALLBACK=1` in your shell profile.
- The helper auto-sets `GREEUM_DISABLE_ST=1` so first-run requests skip heavy sentence-transformer downloads. Unset it (or set to `0`) if you already warmed the model cache and want semantic embeddings.
- Prefer the built-in warm-up before enabling semantics in long-lived sessions: `greeum mcp warmup` (downloads the default SentenceTransformer model).

### Daily digest

```
greeum-digest --limit 10
```

- Set `GREEUM_SLACK_WEBHOOK=https://hooks.slack.com/services/...` to post straight into Slack/Discord.
- Cron example:
  ```
  0 9 * * * greeum-digest --limit 10 >/tmp/greeum_digest.log 2>&1
  ```

## 3. 팀/온보딩용 템플릿

### Codex CLI
```toml
[mcp_servers.greeum]
command = "greeum"
args    = ["mcp", "serve", "-t", "stdio"]
env     = { "GREEUM_QUIET" = "true", "PYTORCH_ENABLE_MPS_FALLBACK" = "1" }
```
> `greeum setup --start-worker`를 먼저 실행하면 초기 타임아웃을 피할 수 있습니다.

### ClaudeCode / Cursor
- 명령: `greeum mcp serve` (semantic 필요 시 `--semantic`)
- 자동 워커 감지를 위해 `GREEUM_MCP_HTTP=http://127.0.0.1:8820/mcp` 환경 변수를 설정

### Slack/온보딩 메시지 예시
````markdown
1. `pipx install --pip-args "--pre" greeum`
2. `greeum setup --start-worker`
3. `greeum-workflow search "onboarding"`
4. 작업 마무리 후 `greeum-workflow add 0.6 "[Day1] Learned ..."`
````

## 4. 운영 FAQ

| 상황 | 해결 방법 |
|------|-----------|
| STDIO 로그가 많다 | `export GREEUM_QUIET=true` |
| 첫 호출이 느리다 | 워커 자동 워밍업(`greeum setup --start-worker`) |
| DB 오류가 발생 | `greeum migrate doctor --yes` 실행 |
| 의미 검색 활성화 | `greeum mcp warmup` → `greeum mcp serve --semantic` |
| Slack 알림 | `GREEUM_SLACK_WEBHOOK` 설정 후 `greeum-digest` |

---

`search → work → add` 루틴은 한 번 익히면 계속 유지됩니다. 워커가 항상 백그라운드에서 대기하니, 설치 직후 바로 적용해 보세요.

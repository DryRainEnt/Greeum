# Greeum Workflow & Reminder Guide

Turn the `search → work → add` loop into a daily habit. Everything below uses the built-in commands that ship with `greeum==3.1.1rc4.dev1+`.

**First-time checklist**
- `pipx install --pip-args "--pre" greeum`
- `greeum setup` → choose the data directory and (optionally) warm up semantic embeddings
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

## 3. Teams & Onboarding

### Codex CLI

1. `~/.codex/config.toml`
   ```toml
   [mcp_servers.greeum]
   command = "/Users/you/.local/bin/greeum"
   args = ["mcp", "serve", "-t", "stdio"]
   env = { "PYTORCH_ENABLE_MPS_FALLBACK" = "1", "GREEUM_QUIET" = "true" }
   ```
2. Add a checklist snippet:
   - Start prompt: “Before coding, run `greeum-workflow search …`.”
   - Finish prompt: “Wrap up with `greeum-workflow add …`.”

### IDEs / Editors

- VS Code `tasks.json`
  ```json
  {
    "label": "Greeum: capture summary",
    "type": "shell",
    "command": "greeum-workflow",
    "args": ["add", "0.6", "${input:summaryText}"]
  }
  ```
  Use `inputs` to prompt for the summary.
- JetBrains: add an External Tool mapped to `greeum-workflow add …` and bind it to a shortcut.

### New teammates

1. `pipx install --pip-args "--pre" greeum` (Python ≥ 3.11).
2. `greeum setup` (pick the data directory and optionally run the warm-up now).
3. `greeum --version` → check `3.1.1rc4.dev1` or newer.
4. `greeum-workflow search "onboarding"` and `add` a “First-day summary”.
5. Subscribe to the digest in Slack/email.

## 4. Messaging Tone

- Emphasize value: “Yesterday’s decision is one command away”, “Wrap up so the next shift continues instantly.”
- Repeat the message across docs, Slack welcome posts, onboarding decks.
- Keep quick-start instructions short and link back to this guide for detail.

## 5. Ops & Troubleshooting

- **Noise control** – `GREEUM_QUIET=true` keeps STDIO output clean; keep duplicate warnings—they protect data quality.
- **Apple Silicon** – `PYTORCH_ENABLE_MPS_FALLBACK=1` avoids meta-tensor errors when loading sentence-transformers.
- **Semantic mode** – run `greeum mcp warmup` and then start the server with `greeum mcp serve --semantic` once the cache is ready.
- **Database locks** – occasional `database is locked` warnings mean two jobs overlapped; schedule heavy jobs sequentially or run `greeum migrate doctor` during low traffic.

---

With `greeum-workflow` and `greeum-digest`, the `search → work → add` rhythm becomes muscle memory. Automate the reminders, keep the messaging value-focused, and the memories keep flowing.

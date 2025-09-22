# Greeum Workflow & Reminder Guide

This playbook turns the `search → work → add` routine into a habit—for Codex CLI users and for anyone running the Greeum MCP server locally.

## 1. Daily Flow (human-friendly)

1. **Kick-off with context** – run `./scripts/greeum_workflow.sh search "<topic>"` to pull related memories before you start.
2. **Do the work** – keep Codex open; if new context surfaces, keep notes inline.
3. **Finish with `add_memory`** – `./scripts/greeum_workflow.sh add 0.6 "<summary>"` the moment you’re done. Quick heuristics:
   - summarize the outcome, key decisions, blockers
   - tag the date or use a prefix like `[CodexExperience-YYYY-MM-DD]`
4. **Weekly reflection** – run `./scripts/greeum_daily_digest.sh` (or let cron trigger it) to review what has been stored.

## 2. Quick Automation Blocks

### CLI helper (`scripts/greeum_workflow.sh`)

```
./scripts/greeum_workflow.sh search "deployment checklist"
./scripts/greeum_workflow.sh add 0.55 "[CodexExperience-2025-09-19] Codex STDIO integration validated."
./scripts/greeum_workflow.sh recap 10
```

- The script resolves `greeum` automatically. Override with `GREEUM_CLI_BIN=/path/to/greeum` if you need a venv build.
- For quiet STDIO logs add `export GREEUM_QUIET=true` in your shell profile.

### Daily digest skeleton (`scripts/greeum_daily_digest.sh`)

- Sends a Markdown digest to STDOUT by default.
- Set `GREEUM_SLACK_WEBHOOK` to post the digest to Slack/Discord.
- Cron example (`crontab -e`):
  ```
  0 9 * * * /Users/you/DevRoom/Greeum/scripts/greeum_daily_digest.sh >/tmp/greeum_digest.log 2>&1
  ```

## 3. Teams & Onboarding

### Codex CLI

1. Ensure `~/.codex/config.toml` uses STDIO:
   ```toml
   [mcp_servers.greeum]
   command = "/Users/yourname/.local/bin/greeum"
   args = ["mcp", "serve", "-t", "stdio"]
   ```
2. Add `./scripts/greeum_workflow.sh` to your `$PATH` (or create a shell alias).
3. Add a Codex checklist snippet:
   - Start prompt: “Before coding, run `greeum` search and paste anything relevant.”
   - Exit prompt: “Wrap up by calling `greeum` add-memory with today’s summary.”

### IDEs / Editors

- VS Code tasks.json example:
  ```json
  {
    "label": "Greeum: capture summary",
    "type": "shell",
    "command": "./scripts/greeum_workflow.sh",
    "args": ["add", "0.6", "${input:summaryText}"],
    "options": {"cwd": "${workspaceFolder}"}
  }
  ```
  Prompt for input using `inputs` block.
- JetBrains: map the script to an External Tool so `⌥⌘G` asks for a summary and writes to Greeum.

### New teammates

1. `pipx install --pip-args "--pre" greeum` (requires Python ≥ 3.11).
2. `greeum --version` → verify `3.1.1rc4.dev1` or later.
3. Run `./scripts/greeum_workflow.sh search "onboarding"` and `add` a “First-day summary”.
4. Subscribe to the daily digest (Slack channel, email, etc.).

## 4. Messaging Tone

- Lead with value: “Pull yesterday’s decision instantly”, “Wrap up with one command so the whole team can pick up tomorrow.”
- Repeat the message—docs, Slack welcome post, onboarding decks.
- Keep instructions short; link to this guide for details.

## 5. Ops & Troubleshooting

- **Noise control** – set `GREEUM_QUIET=true`. Keep duplicate warnings: they help maintain quality.
- **Apple Silicon** – export `PYTORCH_ENABLE_MPS_FALLBACK=1` if you see meta tensor errors.
- **Database locks** – occasional `database is locked` warnings mean tasks overlapped; schedule heavy jobs sequentially or run `greeum migrate doctor` during low-traffic windows.

---

With these pieces in place, “search → work → add” becomes muscle memory. Automate the reminders, keep the messaging focused on productivity, and the memories keep flowing. EOF

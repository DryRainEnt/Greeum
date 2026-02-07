# Greeum Quick Start

## 1. Install

```bash
pip install greeum
```

Python 3.10+ required. Linux, macOS, WSL supported.

## 2. Setup

```bash
greeum setup
```

The wizard guides you through three modes:

| Mode | When to use | Command |
|------|-------------|---------|
| **Local** | Single machine | `greeum setup` → select [1] |
| **Server** | Share across devices | `greeum setup --server` |
| **Remote** | Connect to a server | `greeum setup --remote URL --api-key KEY` |

**Server mode** handles everything automatically:
- Embedding model download
- API key generation
- Tailscale installation (optional, for remote access)
- systemd service registration (auto-start on boot)

## 3. Connect MCP Client

### Claude Code
```bash
claude mcp add greeum -- greeum mcp serve -t stdio
```

### Cursor
Add to MCP settings:
```json
{
  "greeum": {
    "command": "greeum",
    "args": ["mcp", "serve", "-t", "stdio"]
  }
}
```

### Codex
`~/.codex/config.toml`:
```toml
[mcp_servers.greeum]
command = "greeum"
args    = ["mcp", "serve", "-t", "stdio"]
```

## 4. Usage Pattern

1. **Search** before work — pull in relevant context
2. **Work** on the task
3. **Add** a summary when done

```bash
greeum memory search "auth flow" --count 5
# ... do work ...
greeum memory add "Migrated to JWT auth" --importance 0.7
```

## 5. Useful Commands

| Command | Description |
|---------|-------------|
| `greeum config show` | View current configuration |
| `greeum config test` | Test remote server connection |
| `greeum slots status` | View STM slot status |
| `greeum doctor` | Run system diagnostics |
| `greeum mcp warmup` | Pre-download embedding model |

---

For detailed documentation, see the [docs/](.) directory.

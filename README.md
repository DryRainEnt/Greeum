# Greeum

[![PyPI version](https://badge.fury.io/py/greeum.svg)](https://badge.fury.io/py/greeum)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**Persistent memory for AI agents** — no more context loss between sessions.

Greeum is an open-source memory module that gives LLM agents long-term memory. Store memories on your own workstation, access them from anywhere, and never lose context again.

<p align="center">
  <a href="README.md"><strong>English</strong></a> · <a href="docs/README_ko.md">한국어</a>
</p>

---

## Quick Start

```bash
# Install
pip install greeum

# Setup (interactive wizard)
greeum setup

# Test
greeum memory add "My first memory"
greeum memory search "first"
```

That's it. Greeum is ready to use with your MCP client.

---

## Setup Modes

`greeum setup` provides three modes depending on your use case:

### Local (default)

Store memories on this computer only.

```bash
greeum setup
# Select [1] Local
```

### Server

Turn this computer into a Greeum server accessible from anywhere.
Handles API key generation, Tailscale networking, and auto-start on boot.

```bash
greeum setup --server
```

```
[1/5] Data directory        ~/.greeum  ✓
[2/5] Embedding model       ready  ✓
[3/5] API server             port 8400, key generated  ✓
[4/5] Tailscale network     connected  ✓
[5/5] System service        auto-start enabled  ✓
```

### Remote

Connect to an existing Greeum server — one command.

```bash
greeum setup --remote http://my-server:8400 --api-key grm_xxxxx
```

All MCP tools and CLI commands will use the remote server automatically.

---

## MCP Integration

Once `greeum setup` is complete, connect your MCP client:

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

> Greeum MCP is supported on Linux, macOS, and WSL. On Windows, use WSL.

---

## MCP Tools

Greeum provides these tools to your AI agent via MCP:

| Tool | Description |
|------|-------------|
| `add_memory` | Store a memory with optional importance score |
| `search_memory` | Semantic search across all memories |
| `get_memory_stats` | View memory count, slots, and system health |
| `usage_analytics` | Analyze usage patterns over time |
| `system_doctor` | Run diagnostics and auto-repair |
| `analyze` | Summarize recent activity and slot status |

### How agents use Greeum

1. **Search** before starting work — retrieve relevant context
2. **Work** on the task with full context
3. **Add** a summary when done — preserve decisions and outcomes

```json
{ "name": "search_memory", "arguments": { "query": "auth refactor", "limit": 5 } }
{ "name": "add_memory", "arguments": { "content": "Switched to JWT tokens for auth", "importance": 0.7 } }
```

---

## CLI Reference

```bash
# Memory operations
greeum memory add "context to remember"
greeum memory add "important note" --importance 0.8
greeum memory search "keyword" --count 5

# Slot management
greeum slots status
greeum slots set A 123      # Pin memory #123 to slot A

# Server management
greeum config show           # View current configuration
greeum config mode local     # Switch to local mode
greeum config mode remote    # Switch to remote mode
greeum config test           # Test remote connection

# Maintenance
greeum doctor                # System diagnostics
greeum mcp warmup            # Pre-download embedding model
```

---

## Architecture

```
┌─────────────────────────────────────────────┐
│               Your Workstation               │
│                                             │
│  greeum api serve (:8400)                   │
│  ├── Semantic Search (sentence-transformers)│
│  ├── STM Slots (A/B/C context anchors)     │
│  ├── Branch-aware LTM storage (SQLite)     │
│  └── API Key authentication                │
│                                             │
│  Accessible via Tailscale from anywhere     │
└─────────────────────────────────────────────┘
        ▲               ▲               ▲
        │               │               │
   Claude Code       Cursor          Codex
   (MCP/STDIO)     (MCP/STDIO)    (MCP/STDIO)
```

---

## Documentation

- [Quick Start Guide](docs/QUICKSTART.md)
- [Getting Started](docs/get-started.md)
- [Anchors Guide](docs/anchors-guide.md)
- [API Reference](docs/api-reference.md)
- [Troubleshooting](docs/troubleshooting.md)

---

## License

MIT License — see [LICENSE](LICENSE).

**Greeum** · Persistent memory for AI — built and maintained by the community.

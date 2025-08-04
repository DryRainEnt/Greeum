# Greeum

[![PyPI version](https://badge.fury.io/py/greeum.svg)](https://badge.fury.io/py/greeum)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

AI conversations that remember everything.
No more repeating context every time.

## ⚡ Quick Start

```bash
# Install
pip install greeum

# Add your first memory
greeum memory add "Started working on the new dashboard project"

# Search later
greeum memory search "dashboard project"
```

That's it. Your AI now remembers.

## ✨ What It Does

🧠 **Remembers context** - AI recalls previous conversations and decisions
⚡ **280x faster search** - Checkpoint-based memory retrieval
🔄 **Works with any AI** - GPT, Claude, or your custom model
🛡️ **Your data stays yours** - Local storage, no cloud required

## 🔧 Installation

### Basic Setup
```bash
pip install greeum
```

### With All Features
```bash
pip install greeum[all]  # includes vector search, embeddings
```

### For Claude Code Users
```bash
# Install and configure MCP server
pip install greeum
greeum mcp configure
```

## 📝 Usage

### Adding Memories
```bash
# Add important context
greeum memory add "Client prefers minimal UI design"

# Add with expiration
greeum stm add "Working on login page today" --ttl 24h
```

### Searching
```bash
# Find relevant memories
greeum memory search "UI design preferences" --count 5

# Search recent context
greeum stm search "login" --recent
```

### Python API
```python
from greeum import BlockManager, DatabaseManager

# Initialize
db_manager = DatabaseManager()
memory = BlockManager(db_manager)

# Add memory
memory.add_memory("User wants dark mode toggle")

# Search
results = memory.search_memories("dark mode", top_k=3)
```

## 🤖 Claude Integration

### Setup MCP Server
Add to your Claude Desktop config:

```json
{
  "mcpServers": {
    "greeum": {
      "command": "greeum",
      "args": ["mcp", "serve"],
      "env": {
        "GREEUM_DATA_DIR": "/path/to/your/data"
      }
    }
  }
}
```

### Available Tools
- `add_memory` - Store important context
- `search_memory` - Find relevant memories
- `analyze_patterns` - Discover insights

## 📚 Documentation

- [Getting Started](docs/get-started.md) - Installation and first steps
- [API Reference](docs/api-reference.md) - Complete API documentation
- [MCP Integration](docs/mcp-integration.md) - Claude Code setup

## 🏗️ Architecture

```
Your Input → Working Memory → Cache → Checkpoints → Long-term Storage
             0.04ms          0.08ms   0.7ms        Permanent
```

Four-layer memory system optimized for speed and relevance.

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch
3. Submit a pull request

See [CONTRIBUTING.md](CONTRIBUTING.md) for details.

## 📄 License

MIT License - see [LICENSE](LICENSE) file.

---

**Greeum** - Memory for AI that actually works.
Made with ❤️ by the open source community.
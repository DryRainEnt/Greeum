# Greeum

AI conversations that remember everything.

## Quick Start

```bash
# Install
pip install greeum

# Add your first memory
greeum memory add "Started working on the dashboard project"

# Search memories
greeum memory search "dashboard"
```

## Claude Integration

```bash
pip install greeum
```

Add to Claude Desktop config:
```json
{
  "mcpServers": {
    "greeum": {
      "command": "greeum",
      "args": ["mcp", "serve"]
    }
  }
}
```

Restart Claude. Your AI now remembers.

**Config location:** [macOS/Windows/Linux paths →](docs/claude-setup.md)

## What You Get

🧠 **Permanent Memory** - Context persists across conversations  
🔍 **Smart Search** - Find relevant past conversations  
⚡ **Instant Setup** - Works out of the box  
🔒 **Private** - All data stays on your machine

## CLI Usage

```bash
greeum memory add "Important project decision"
greeum memory search "project" --count 5
greeum anchors set A 123  # Pin memory to quick slot
```

## Python API

```python
from greeum import BlockManager, DatabaseManager

db = DatabaseManager()
memory = BlockManager(db)
memory.add_block(context="User prefers dark mode", importance=0.8)
```

## Documentation

- [Complete Claude Setup](docs/claude-setup.md)
- [API Reference](docs/api-reference.md)  
- [Troubleshooting](docs/troubleshooting.md)
- [What's New in v2.2.7](docs/whats-new.md)

## Need Help?

- 📖 [Documentation](docs/)
- 🐛 [Issues](https://github.com/DryRainEnt/Greeum/issues)
- 💬 [Discussions](https://github.com/DryRainEnt/Greeum/discussions)
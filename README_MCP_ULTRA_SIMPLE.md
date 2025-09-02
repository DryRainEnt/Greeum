## 🤖 Claude Integration

### Quick Setup
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

Restart Claude Desktop. Done.

**Config file location:**
- macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`
- Windows: `%APPDATA%\Claude\claude_desktop_config.json`
- Linux: `~/.config/claude-desktop/claude_desktop_config.json`

### Available Tools
- `add_memory` - Store important context
- `search_memory` - Find relevant memories  
- `get_memory_stats` - View memory statistics

**Need help?** → [Complete setup guide](docs/claude-setup.md) | [Troubleshooting](docs/troubleshooting.md)
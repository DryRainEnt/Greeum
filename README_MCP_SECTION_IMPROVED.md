# 🤖 Claude Integration (Updated for v2.2.7)

## Unified MCP Server - Zero Configuration Required

Greeum v2.2.7 introduces a revolutionary unified MCP server that **automatically detects your environment**:

| Environment | Adapter Used | Optimized For |
|-------------|--------------|---------------|
| **WSL** | FastMCP | Perfect stdin/stdout compatibility |
| **PowerShell** | FastMCP | Windows terminal safety |
| **macOS** | JSON-RPC | Native performance |
| **Linux** | JSON-RPC | Maximum speed |

**No manual configuration needed** - just works everywhere!

## Quick Setup (30 seconds)

### 1. Install Greeum
```bash
pip install greeum
```

### 2. Add to Claude Desktop

**Configuration File Location:**
- **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`
- **Linux**: `~/.config/claude-desktop/claude_desktop_config.json`

**Basic Configuration (Works Everywhere):**
```json
{
  "mcpServers": {
    "greeum": {
      "command": "greeum",
      "args": ["mcp", "serve", "-t", "stdio"],
      "env": {
        "GREEUM_DATA_DIR": "/path/to/your/data"
      }
    }
  }
}
```

### 3. Restart Claude Desktop
That's it! Your AI now has permanent memory.

## Available Tools

| Tool | Purpose | Example |
|------|---------|---------|
| `add_memory` | Store important context | Project decisions, preferences |
| `search_memory` | Find relevant memories | Past conversations, decisions |
| `get_memory_stats` | System status | Memory usage, health check |
| `usage_analytics` | Usage insights | Patterns, optimization tips |

## What's New in v2.2.7

### 🎯 Major Improvements
- ✅ **Environment Auto-Detection**: Works seamlessly across all platforms
- ✅ **Unified Architecture**: Single server replaces 8 fragmented files
- ✅ **AsyncIO Safety**: Eliminated all runtime conflicts
- ✅ **100% Backward Compatible**: No changes to existing workflows
- ✅ **Enhanced Reliability**: 100% test coverage with comprehensive validation

### 🔧 Technical Highlights
- **Smart Adapter Selection**: Automatically chooses FastMCP or JSON-RPC based on environment
- **Runtime Safety**: Prevents AsyncIO event loop conflicts
- **Performance Optimized**: <1s response times across all tools
- **Security First**: Local-only operation, secure data handling

## Platform-Specific Examples

<details>
<summary><strong>WSL (Windows Subsystem for Linux)</strong></summary>

```json
{
  "mcpServers": {
    "greeum": {
      "command": "wsl",
      "args": ["greeum", "mcp", "serve", "-t", "stdio"],
      "env": {
        "GREEUM_DATA_DIR": "/mnt/c/Users/YourName/greeum-data"
      }
    }
  }
}
```
</details>

<details>
<summary><strong>PowerShell (Windows)</strong></summary>

```json
{
  "mcpServers": {
    "greeum": {
      "command": "powershell",
      "args": ["-Command", "greeum mcp serve -t stdio"],
      "env": {
        "GREEUM_DATA_DIR": "C:\\Users\\YourName\\greeum-data"
      }
    }
  }
}
```
</details>

<details>
<summary><strong>macOS/Linux (Native)</strong></summary>

```json
{
  "mcpServers": {
    "greeum": {
      "command": "greeum", 
      "args": ["mcp", "serve", "-t", "stdio"],
      "env": {
        "GREEUM_DATA_DIR": "/Users/yourname/greeum-data"
      }
    }
  }
}
```
</details>

## Troubleshooting

### Quick Diagnostics
```bash
# Test installation
greeum --version

# Test memory functionality  
greeum memory add "test memory"

# Test MCP server
timeout 5s greeum mcp serve -t stdio
```

### Common Solutions
- **"Command not found"**: Ensure `pip install greeum` completed successfully
- **"Permission denied"**: Check data directory permissions (`chmod 700 /path/to/data`)
- **"Connection failed"**: Verify JSON configuration syntax and restart Claude Desktop

### Debug Mode
```bash
GREEUM_LOG_LEVEL=DEBUG greeum mcp serve -t stdio
```

**Need help?** Check logs in `~/.greeum/` or [open an issue](https://github.com/DryRainEnt/Greeum/issues).

---

**🎉 Upgrade Notice**: Greeum v2.2.7 is a major reliability update. All existing configurations continue to work without changes, but now with enhanced stability and performance across all platforms.
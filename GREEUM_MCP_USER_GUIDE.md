# 🧠 Greeum MCP Server - Complete User Guide

[![Version](https://img.shields.io/badge/version-v2.2.7-blue.svg)](https://pypi.org/project/greeum/)
[![Claude Desktop](https://img.shields.io/badge/Claude%20Desktop-✅%20Compatible-green.svg)](https://claude.ai/desktop)
[![Cross Platform](https://img.shields.io/badge/Platform-WSL%20%7C%20PowerShell%20%7C%20macOS%20%7C%20Linux-lightgrey.svg)]()

Universal memory for your AI conversations. Never repeat context again.

## ⚡ Quick Start (30 seconds)

```bash
# 1. Install Greeum
pip install greeum

# 2. Test installation
greeum --version

# 3. Add to Claude Desktop config
# See "Claude Desktop Setup" below for your platform
```

That's it! Your AI now has permanent memory across conversations.

---

## 🤖 Claude Desktop Setup

### Automatic Environment Detection
Greeum v2.2.7 **automatically detects your environment** and chooses the optimal adapter:
- **WSL/PowerShell**: Uses FastMCP for perfect compatibility
- **macOS/Linux**: Uses JSON-RPC for maximum performance  
- **No configuration needed** - just works!

### Configuration File Location

| Platform | Configuration File Path |
|----------|------------------------|
| **macOS** | `~/Library/Application Support/Claude/claude_desktop_config.json` |
| **Windows** | `%APPDATA%\\Claude\\claude_desktop_config.json` |
| **Linux** | `~/.config/claude-desktop/claude_desktop_config.json` |

### Basic Configuration (Recommended)

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

### Advanced Configuration (Optional)

```json
{
  "mcpServers": {
    "greeum": {
      "command": "/usr/local/bin/greeum",
      "args": ["mcp", "serve", "-t", "stdio"],
      "env": {
        "GREEUM_DATA_DIR": "/Users/yourname/greeum-data",
        "GREEUM_LOG_LEVEL": "INFO",
        "PYTHONPATH": "/path/to/greeum/if/needed"
      }
    }
  }
}
```

---

## 🔧 Platform-Specific Setup

### WSL (Windows Subsystem for Linux)
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

### PowerShell (Windows)
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

### macOS/Linux (Direct)
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

---

## 🌐 HTTP MCP Server (Codex CLI & OpenAI)

Use the built-in HTTP transport when a client requires a URL-based MCP endpoint:

```bash
pip install greeum
greeum mcp serve -t http --host 0.0.0.0 --port 8800
```

Register the endpoint with your agent (example Codex CLI configuration):

```json
{
  "mcpServers": {
    "greeum": {
      "server_url": "http://127.0.0.1:8800/mcp",
      "allowed_tools": ["add_memory", "search_memory", "get_memory_stats", "usage_analytics"]
    }
  }
}
```

The server exposes `POST /mcp` for JSON-RPC 2.0 requests and `GET /healthz` for readiness checks. Keep the port firewalled if you expose it beyond localhost, and supply authorization headers through your client when required.

---

## 🛡️ Security Best Practices

### ⚠️ Important Security Considerations

1. **Data Directory Permissions**
   ```bash
   # Ensure only your user can access the data
   chmod 700 /path/to/your/greeum-data
   ```

2. **Environment Variables**
   - Never commit API keys to version control
   - Use absolute paths for data directories
   - Regularly backup your memory data

3. **Network Security**
   - Greeum operates locally by default
   - No network access required for basic functionality
   - Memory data stays on your machine

### 📁 Recommended Data Directory Structure
```
~/greeum-data/
├── memory.db          # Main memory database
├── analytics.db       # Usage analytics (optional)
├── logs/              # Application logs
└── backups/           # Automatic backups (coming soon)
```

---

## ✅ Available Tools

Once configured, these tools become available in Claude:

| Tool | Description | Example Usage |
|------|-------------|---------------|
| **add_memory** | Store important context permanently | Remember project decisions, user preferences |
| **search_memory** | Find relevant past conversations | Retrieve previous discussions about topics |
| **get_memory_stats** | View memory system status | Check storage usage, system health |
| **usage_analytics** | Analyze memory usage patterns | Understand how your memory is being used |

---

## 🔧 Troubleshooting

### Common Issues & Solutions

#### ❌ "Command not found: greeum"
```bash
# Check if greeum is installed
pip show greeum

# If not installed
pip install greeum

# Check PATH
which greeum
```

#### ❌ "Failed to connect to MCP server"
1. **Verify configuration file syntax**:
   ```bash
   # Validate JSON
   python -c "import json; json.load(open('claude_desktop_config.json'))"
   ```

2. **Check logs** (macOS):
   ```bash
   tail -f ~/Library/Logs/Claude/mcp*.log
   ```

3. **Test server manually**:
   ```bash
   greeum mcp serve -t stdio
   # Should start without errors
   ```

#### ❌ "Permission denied" errors
```bash
# Fix data directory permissions
mkdir -p ~/greeum-data
chmod 700 ~/greeum-data

# Ensure greeum can write logs
mkdir -p ~/.greeum
chmod 755 ~/.greeum
```

#### ❌ Environment detection issues
```bash
# Force environment check
greeum mcp serve -t stdio --debug

# Check environment variables
echo $OS
echo $TERM
uname -a
```

### Debug Mode
```bash
# Enable detailed logging
GREEUM_LOG_LEVEL=DEBUG greeum mcp serve -t stdio
```

### Getting Help
- Check logs in `~/.greeum/` directory
- Test CLI commands: `greeum memory add "test"`
- Verify MCP server: `greeum mcp serve --help`

---

## 🚀 What Makes Greeum v2.2.7 Special

### ✨ Unified Architecture
- **Before**: 8 fragmented server files causing confusion
- **After**: 1 unified server with automatic environment detection
- **Result**: Zero configuration hassles

### ⚡ Environment Auto-Detection
```
🔍 Environment Detection:
├── WSL detected → FastMCP Adapter (optimal compatibility)
├── PowerShell detected → FastMCP Adapter (stdin/stdout safe)
├── macOS detected → JSON-RPC Adapter (maximum performance)
└── Linux detected → JSON-RPC Adapter (native speed)
```

### 🛡️ AsyncIO Safety
- **Problem**: Runtime conflicts in mixed Python environments
- **Solution**: Smart event loop detection and management
- **Benefit**: Never crashes due to event loop conflicts

### 🔄 100% Backward Compatible
- All existing commands work identically
- No data migration required
- Drop-in replacement for previous versions

---

## 📚 Additional Resources

- [Greeum Documentation](https://github.com/DryRainEnt/Greeum)
- [Model Context Protocol](https://modelcontextprotocol.io/)
- [Claude Desktop](https://claude.ai/desktop)
- [Troubleshooting Guide](https://github.com/DryRainEnt/Greeum/issues)

---

## 🆘 Need Help?

1. **Check the logs**: `~/.greeum/` directory
2. **Test manually**: `greeum memory add "test message"`  
3. **Verify MCP**: `greeum mcp serve --help`
4. **Open an issue**: [GitHub Issues](https://github.com/DryRainEnt/Greeum/issues)

---

*Last updated: 2025-09-01 for Greeum v2.2.7*

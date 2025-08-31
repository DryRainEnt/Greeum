# 🚀 Get Started with Greeum

Complete installation and setup guide for Greeum v2.2.5 with anchored memory system.

## 📋 Table of Contents

- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [First Setup](#first-setup)
- [Basic Usage](#basic-usage)
- [Anchor System](#anchor-system)
- [MCP Integration](#mcp-integration)
- [Troubleshooting](#troubleshooting)

## Prerequisites

- **Python 3.10+** (3.12 recommended)
- **pipx** (recommended) or **pip**
- **Operating System**: macOS, Linux, Windows

### Check Python Version

```bash
python3 --version
# Should output: Python 3.10.x or higher
```

### Install pipx (Recommended)

```bash
# macOS (using Homebrew)
brew install pipx
pipx ensurepath

# Linux (Ubuntu/Debian)
sudo apt install pipx
pipx ensurepath

# Windows
pip install --user pipx
pipx ensurepath
```

## Installation

### Option 1: Install with pipx (Recommended)

```bash
# Install latest Greeum with anchor system
pipx install "greeum>=2.2.5"

# Verify installation
python3 -m greeum.cli --version
```

### Option 2: Install with pip

```bash
# Install Greeum
pip install greeum

# Verify installation
greeum --version
```

### Option 3: Install with All Dependencies

For full feature support including advanced vector search:

```bash
# Install with all optional dependencies
pipx install "greeum[all]"

# Or with pip
pip install "greeum[all]"
```

## First Setup

### 1. Initialize Data Directory

Greeum will automatically create its data directory on first use, but you can customize the location:

```bash
# Set custom data directory (optional)
export GREEUM_DATA_DIR="/path/to/your/data"

# Or use default location (~/.greeum/)
```

### 2. Create Your First Memory

```bash
# Add your first memory (v2.2.5+ syntax)
greeum memory add "I'm starting to use Greeum for memory management. This is my first memory entry."

# Verify it was created
greeum memory search "Greeum" --count 5
```

### 3. Test Basic Functionality

```bash
# Add a few more memories
greeum memory add "Working on a Python project with FastAPI"
greeum memory add "Meeting with team about Q4 goals"

# Search memories
greeum memory search "python" --count 3
greeum memory search "meeting" --count 3

# View recent memories
greeum recent-memories --count 10
```

## Basic Usage

### Adding Memories

```bash
# Add memory with content (v2.2.5+ syntax)
greeum memory add "Your memory content here"

# Add short-term memory with TTL
greeum stm add "Working on login page today" --ttl 24h

# Add memory with importance (via Python API)
# CLI focuses on simplicity, use Python API for advanced options
```

### Searching Memories

```bash
# Search memories with query
greeum memory search "project python" --count 5

# Recent memories
greeum recent-memories --count 10

# Anchor-based search (v2.2.5+ NEW!)
greeum memory search "meeting" --slot A --radius 2
```

## Anchor System (v2.2.5+)

### Understanding Anchors

Anchors are fixed reference points in your memory graph that enable faster, more contextually relevant searches.

### Basic Anchor Operations

```bash
# Check current anchor status
greeum anchors status

# Set anchors to important memories
greeum anchors set A 1     # Pin memory block #1 to slot A
greeum anchors set B 2     # Pin memory block #2 to slot B

# Pin anchors to prevent auto-movement
greeum anchors pin A       # Anchor A won't move automatically

# Search near anchors (faster than global search)
greeum memory search "python" --slot A --radius 3

# Clear all anchors
greeum anchors clear
```

### Memory Quality Management

```bash
# Check system statistics
greeum recent-memories --count 5

# Check quality of file
greeum quality -f "/path/to/file.txt"

# Specify importance level for quality check
greeum quality -c "Important content" -i 0.8
```

### Usage Analytics

```bash
# View usage analytics (last 7 days)
greeum analytics

# View analytics for specific period
greeum analytics -d 30

# Detailed analytics report
greeum analytics -d 30 --detailed
```

### Memory Optimization

```bash
# Run memory optimization analysis
greeum optimize

# Run with automatic optimization
greeum optimize --auto-optimize
```

### Short-term Memory

```bash
# Add to short-term memory
greeum stm "Temporary note for current session"

# View short-term memories
greeum get-stm

# View specific number of STM entries
greeum get-stm -c 10
```

### Advanced Operations

```bash
# Generate enhanced prompt
greeum prompt -i "What did we discuss in yesterday's meeting?"

# Clear different types of memory
greeum clear stm        # Clear short-term memory
greeum clear cache      # Clear waypoint cache
greeum clear blocks     # Clear all blocks (with backup)
greeum clear all        # Clear everything

# Verify blockchain integrity
greeum verify
```

## MCP Integration

### Setting up with Claude Code

#### 1. Verify Greeum Installation

```bash
# Check version (should be v2.0.5 or higher)
greeum --version

# Test MCP server
python3 -m greeum.mcp.claude_code_mcp_server --help
```

#### 2. Configure Claude Desktop

Edit your Claude Desktop configuration file:

**macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
**Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

```json
{
  "mcpServers": {
    "greeum": {
      "command": "python3",
      "args": [
        "-m", "greeum.mcp.claude_code_mcp_server"
      ],
      "env": {
        "GREEUM_DATA_DIR": "/your/preferred/data/path"
      }
    }
  }
}
```

#### 3. Restart Claude Desktop

Restart Claude Desktop application to load the new MCP configuration.

#### 4. Verify Connection

In Claude Code, run:

```bash
claude mcp list
```

You should see `greeum` server listed with "✓ Connected" status.

#### 5. Test MCP Tools

The following tools will be available in Claude Code:

- **add_memory**: Add new memories with quality validation
- **search_memory**: Search existing memories with context
- **get_memory_stats**: View memory system statistics
- **ltm_analyze**: Analyze long-term memory patterns
- **stm_add**: Add short-term memories
- **quality_check**: Verify memory quality
- **check_duplicates**: Check for duplicate memories
- **usage_analytics**: Get usage analytics reports
- **ltm_verify**: Verify memory integrity
- **ltm_export**: Export memory data
- **stm_promote**: Promote STM to LTM
- **stm_cleanup**: Clean up short-term memory

### Alternative MCP Servers

For different use cases, Greeum provides multiple MCP server options:

```bash
# Minimal MCP server (lightweight)
python3 -m greeum.mcp.minimal_mcp_server

# Universal MCP server (compatible with multiple MCP hosts)
python3 -m greeum.mcp.universal_mcp_server

# Working MCP server (development/testing)
python3 -m greeum.mcp.working_mcp_server
```

## Troubleshooting

### Common Issues

#### 1. Installation Problems

```bash
# If pipx installation fails
pip install --user pipx
python3 -m pipx install greeum

# If Python version issues
pyenv install 3.12.0
pyenv global 3.12.0
pipx install greeum
```

#### 2. Permission Issues

```bash
# Fix data directory permissions
chmod 755 ~/.greeum
chmod 644 ~/.greeum/*

# Or use custom directory
export GREEUM_DATA_DIR="/path/with/write/access"
```

#### 3. MCP Connection Issues

```bash
# Check MCP server directly
python3 -m greeum.mcp.claude_code_mcp_server --test

# Verify configuration path
echo $HOME/Library/Application\ Support/Claude/claude_desktop_config.json

# Check logs
tail -f ~/.greeum/logs/mcp.log
```

#### 4. Memory Issues

```bash
# Verify memory integrity
greeum verify

# Reset if corrupted
greeum clear all

# Restore from backup
cp ~/.greeum/backup/block_memory_*.jsonl ~/.greeum/block_memory.jsonl
```

### Getting Help

If you encounter issues:

1. **Check version**: `greeum --version`
2. **Review logs**: Check `~/.greeum/logs/` directory
3. **Test basic functionality**: Try `greeum add -c "test"` and `greeum search`
4. **Contact support**: playtart@play-t.art

### Performance Optimization

For better performance:

```bash
# Install with all dependencies for vector search
pipx install "greeum[all]"

# Optimize memory usage
greeum optimize --auto-optimize

# Clean up old data
greeum clear cache
```

## Next Steps

- **[API Reference](api-reference.md)**: Explore the complete API
- **[Tutorials](tutorials.md)**: Learn advanced usage patterns
- **[Developer Guide](developer_guide.md)**: Contribute to Greeum

## Configuration Options

### Environment Variables

```bash
# Data directory location
export GREEUM_DATA_DIR="/custom/path"

# Log level
export GREEUM_LOG_LEVEL="DEBUG"

# Database type (sqlite/postgresql)
export GREEUM_DB_TYPE="sqlite"

# OpenAI API key (for embeddings)
export OPENAI_API_KEY="your-key-here"
```

### Configuration File

Create `~/.greeum/config.json`:

```json
{
  "database": {
    "type": "sqlite",
    "path": "memory.db"
  },
  "embeddings": {
    "model": "sentence-transformers",
    "cache": true
  },
  "quality": {
    "auto_validate": true,
    "threshold": 0.7
  },
  "analytics": {
    "enabled": true,
    "retention_days": 90
  }
}
```

---

**Congratulations!** You're now ready to use Greeum for intelligent memory management. Visit [greeum.app](https://greeum.app) for more resources and updates.
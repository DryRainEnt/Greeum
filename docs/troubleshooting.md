# Troubleshooting Greeum MCP Server

## Quick Diagnostics

```bash
# Check if Greeum is installed
greeum --version

# Test basic functionality
greeum memory add "test message"

# Test MCP server (should start and stop after 5 seconds)
timeout 5s greeum mcp serve -t stdio
```

## Common Issues

### ❌ "Command not found: greeum"

**Problem**: Greeum is not installed or not in PATH

**Solutions**:
```bash
# Check if installed
pip show greeum

# Install if missing
pip install greeum

# Check PATH (should show greeum location)
which greeum

# If using virtual environment, activate it first
source venv/bin/activate  # Linux/macOS
# or
venv\Scripts\activate     # Windows
```

### ❌ "Failed to connect to MCP server"

**Problem**: Claude Desktop cannot connect to Greeum MCP server

**Solutions**:

1. **Check configuration file syntax**:
   ```bash
   # Validate JSON (should not show errors)
   python -c "import json; print('✅ Valid JSON' if json.load(open('claude_desktop_config.json')) else '❌ Invalid JSON')"
   ```

2. **Verify configuration file location**:
   - **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
   - **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`  
   - **Linux**: `~/.config/claude-desktop/claude_desktop_config.json`

3. **Test server manually**:
   ```bash
   # Should start without immediate errors
   greeum mcp serve -t stdio
   
   # Press Ctrl+C to stop
   ```

4. **Check Claude Desktop logs**:
   ```bash
   # macOS
   tail -f ~/Library/Logs/Claude/mcp*.log
   
   # Windows
   # Check %APPDATA%\Claude\Logs\
   
   # Linux  
   tail -f ~/.local/share/Claude/logs/mcp*.log
   ```

### ❌ "Permission denied" errors

**Problem**: Greeum cannot write to data directory

**Solutions**:
```bash
# Create data directory with correct permissions
mkdir -p ~/greeum-data
chmod 700 ~/greeum-data

# Ensure Greeum can write to its config directory
mkdir -p ~/.greeum
chmod 755 ~/.greeum

# For specific data directory (replace path as needed)
export GREEUM_DATA_DIR="/path/to/your/data"
mkdir -p "$GREEUM_DATA_DIR"
chmod 700 "$GREEUM_DATA_DIR"
```

### ❌ "Module not found" errors

**Problem**: Python dependencies missing

**Solutions**:
```bash
# Reinstall with all dependencies
pip install --upgrade greeum

# Check required dependencies
pip install numpy>=1.24.0 sqlalchemy>=2.0.0 click>=8.1.0

# For MCP functionality specifically
pip install mcp>=1.0.0
```

### ❌ Server starts but tools don't appear in Claude

**Problem**: MCP server running but Claude doesn't see tools

**Solutions**:

1. **Restart Claude Desktop completely**:
   - Close Claude Desktop
   - Wait 5 seconds
   - Reopen Claude Desktop

2. **Check server registration**:
   ```json
   {
     "mcpServers": {
       "greeum": {
         "command": "greeum",
         "args": ["mcp", "serve", "-t", "stdio"]
       }
     }
   }
   ```

3. **Verify tools are working**:
   ```bash
   # Enable debug logging
   GREEUM_LOG_LEVEL=DEBUG greeum mcp serve -t stdio
   ```

## Environment-Specific Issues

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

**Common WSL issues**:
- Use `/mnt/c/...` paths for Windows directories
- Ensure WSL can execute `greeum` command
- Check WSL Python environment has Greeum installed

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

**Common PowerShell issues**:
- Use full Windows paths with backslashes
- Ensure PowerShell execution policy allows scripts
- Check that `greeum` command works in PowerShell

## Debug Mode

### Enable Detailed Logging

```bash
# Set debug level
export GREEUM_LOG_LEVEL=DEBUG

# Run with debug output
GREEUM_LOG_LEVEL=DEBUG greeum mcp serve -t stdio

# Check log files
ls ~/.greeum/
cat ~/.greeum/debug.log
```

### Manual Testing

```bash
# Test memory functions directly
greeum memory add "debug test message"
greeum memory search "debug test"

# Test MCP server startup
greeum mcp serve --help

# Check system status
greeum memory stats
```

## Still Need Help?

### Before Opening an Issue

1. **Run diagnostics**:
   ```bash
   greeum --version
   python --version
   pip show greeum
   ```

2. **Check logs**:
   - Greeum logs: `~/.greeum/`
   - Claude Desktop logs: `~/Library/Logs/Claude/` (macOS)

3. **Test basic functionality**:
   ```bash
   greeum memory add "test"
   greeum memory search "test"
   ```

### Get Support

- 🐛 [Open an Issue](https://github.com/DryRainEnt/Greeum/issues)
- 💬 [Discussions](https://github.com/DryRainEnt/Greeum/discussions)
- 📖 [Complete Documentation](../README.md)

### Include This Information

When reporting issues, please include:
- Greeum version (`greeum --version`)
- Operating system and version
- Python version (`python --version`)
- Configuration file (remove any sensitive data)
- Error messages (full text)
- Steps to reproduce
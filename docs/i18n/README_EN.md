# 🧠 Greeum v2.2.5

<p align="center">
  <a href="../../README.md">🇰🇷 한국어</a> |
  <a href="README_EN.md">🇺🇸 English</a> |
  <a href="README_JP.md">🇯🇵 日本語</a> |
  <a href="README_ZH.md">🇨🇳 中文</a>
</p>

Intelligent Memory Management System for LLMs

## 📌 Overview

**Greeum** (pronounced: gri-eum) is a **universal memory module** that connects to any LLM (Large Language Model):

- **Long-term Memory**: Permanent storage of user context, preferences, and goals
- **Short-term Memory**: Session-based important information management
- **Intelligent Search**: Context-based automatic memory recall
- **Quality Management**: Automatic memory quality verification and optimization
- **Multilingual Support**: Full support for Korean, English, Japanese, and Chinese

The name "Greeum" is inspired by the Korean word "그리움" (longing/reminiscence), symbolizing AI's ability to remember and long for the past.

## 🚀 Quick Start

### Installation

```bash
# Install with pipx (recommended) - Latest version with anchor system
pipx install "greeum>=2.2.5"

# Or install with pip
pip install "greeum>=2.2.5"
```

### Basic Usage

```bash
# Add memory (v2.2.5 syntax)
greeum memory add "Started a new project today. Planning to develop a web application with Python."

# Search memories
greeum memory search "project Python" --count 5

# Memory Anchors (NEW in v2.2.5)
greeum anchors status                     # Check anchor status
greeum anchors set A 123                 # Pin memory #123 to slot A
greeum memory search "Python" --slot A   # Search near anchor A

# Add short-term memory
greeum stm add "Temporary note" --ttl 1h

# Run MCP server
python3 -m greeum.mcp.claude_code_mcp_server
```

## 🔑 Key Features

### 📚 Multi-layer Memory System
- **LTM (Long-term Memory)**: Permanent storage with blockchain-like structure
- **STM (Short-term Memory)**: TTL-based temporary memory management
- **Waypoint Cache**: Automatic loading of context-related memories

### 🧠 Intelligent Memory Management
- **Quality Verification**: Automatic quality assessment based on 7 metrics
- **Duplicate Detection**: Prevents duplicates with 85% similarity threshold
- **Usage Analysis**: Pattern analysis and optimization recommendations
- **Auto Cleanup**: Quality-based memory cleanup

### 🔍 Advanced Search
- **Keyword Search**: Tag and keyword-based search
- **Vector Search**: Semantic similarity search
- **Temporal Search**: Natural language time expressions like "3 days ago", "last week"
- **Hybrid Search**: Combined keyword + vector + temporal search

### 🌐 MCP Integration
- **Claude Code**: Complete integration with 12 MCP tools
- **Real-time Sync**: Real-time memory creation/search reflection
- **Quality Verification**: Automatic quality check and feedback

## 🛠️ Advanced Usage

### API Usage
```python
from greeum import BlockManager, STMManager, PromptWrapper

# Initialize memory system
bm = BlockManager()
stm = STMManager()
pw = PromptWrapper()

# Add memory
bm.add_block(
    context="Important meeting content",
    keywords=["meeting", "decisions"],
    importance=0.9
)

# Generate context-based prompt
enhanced_prompt = pw.compose_prompt("What did we decide in the last meeting?")
```

### MCP Tools (for Claude Code)
```
Available tools:
- add_memory: Add new memory
- search_memory: Search memories
- get_memory_stats: Memory statistics
- ltm_analyze: Long-term memory analysis
- stm_add: Add short-term memory
- quality_check: Quality verification
- check_duplicates: Duplicate checking
- usage_analytics: Usage analysis
- ltm_verify: Integrity verification
- ltm_export: Data export
- stm_promote: STM→LTM promotion
- stm_cleanup: STM cleanup
```

## 📊 Memory Quality Management

Greeum v2.0.5 provides intelligent quality management system:

### Quality Assessment Metrics
1. **Length**: Appropriate information volume
2. **Richness**: Meaningful word ratio
3. **Structure**: Sentence/paragraph composition
4. **Language**: Grammar and expression quality
5. **Information Density**: Specific information inclusion
6. **Searchability**: Future search convenience
7. **Temporal Relevance**: Current context relevance

### Automatic Optimization
- **Quality-based importance adjustment**
- **Automatic duplicate memory detection**
- **STM→LTM promotion suggestions**
- **Usage pattern-based recommendations**

## 🔗 Integration Guide

### Claude Code MCP Setup
1. **Check Installation**
   ```bash
   greeum --version  # v2.0.5 or higher
   ```

2. **Claude Desktop Configuration**
   ```json
   {
     "mcpServers": {
       "greeum": {
         "command": "python3",
         "args": ["-m", "greeum.mcp.claude_code_mcp_server"],
         "env": {
           "GREEUM_DATA_DIR": "/path/to/data"
         }
       }
     }
   }
   ```

3. **Verify Connection**
   ```bash
   claude mcp list  # Check greeum server
   ```

### Other LLM Integration
```python
# OpenAI GPT
from greeum.client import MemoryClient
client = MemoryClient(llm_type="openai")

# Local LLM
client = MemoryClient(llm_type="local", endpoint="http://localhost:8080")
```

## 📈 Performance & Benchmarks

- **Response Quality**: 18.6% average improvement (benchmark basis)
- **Search Speed**: 5.04x improvement (with waypoint cache)
- **Re-questioning Reduction**: 78.2% reduction (improved context understanding)
- **Memory Efficiency**: 50% memory usage optimization

## 📚 Documentation & Resources

- **[Get Started](../get-started.md)**: Detailed installation and setup guide
- **[API Reference](../api-reference.md)**: Complete API reference
- **[Tutorials](../tutorials.md)**: Step-by-step usage examples
- **[Developer Guide](../developer_guide.md)**: How to contribute

## 🤝 Contributing

Greeum is an open-source project. Contributions are welcome!

### How to Contribute
1. **Issue Reports**: Report bugs or issues you encounter
2. **Feature Suggestions**: New ideas and improvements
3. **Code Contributions**: Pull requests welcome
4. **Documentation**: Translation and improvement

### Development Environment Setup
```bash
# After downloading source code
pip install -e .[dev]
tox  # Run tests
```

## 📞 Support & Contact

- **📧 Official Email**: playtart@play-t.art
- **🌐 Official Website**: [greeum.app](https://greeum.app)
- **📚 Documentation**: Refer to this README and docs/ folder

## 📄 License

This project is distributed under the MIT License. See the [LICENSE](../../LICENSE) file for details.

## 🏆 Acknowledgments

- **OpenAI**: Embedding API support
- **Anthropic**: Claude MCP platform
- **NumPy**: Efficient vector computation
- **SQLite**: Reliable data storage

---

<p align="center">
  Made with ❤️ by the Greeum Team<br>
  <em>"Making AI more human through memory"</em>
</p>
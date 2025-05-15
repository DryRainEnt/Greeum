# 🧠 MemoryBlockEngine v0.2

An LLM-Independent Memory System Integration Library

## 📌 Overview

**MemoryBlockEngine** is a **universal memory module** that can be attached to any LLM model, designed to:
- Track user's long-term utterances, goals, emotions, and intentions
- Recall memories relevant to the current context
- Function as an "AI with memory"

## 🔑 Key Features

- **Long-Term Memory Blocks**: Blockchain-like structure for immutable memory storage
- **Short-Term Memory Management**: TTL (Time-To-Live) structure for fluid temporary memories
- **Semantic Association**: Keyword/tag/vector-based memory recall system
- **Waypoint Cache**: Automatically retrieves memories related to the current context
- **Prompt Composition**: Automatic generation of LLM prompts that include relevant memories

## ⚙️ Installation

1. Clone the repository
   ```bash
   git clone https://github.com/DryRainEnt/MemoryBlockEngine.git
   cd MemoryBlockEngine
   ```

2. Install dependencies
   ```bash
   pip install -r requirements.txt
   ```

## 🧪 Usage

### CLI Interface

```bash
# Add long-term memory
python cli/memory_cli.py add -c "I started a new project and it's really exciting"

# Search memories by keywords
python cli/memory_cli.py search -k "project,exciting"

# Add short-term memory
python cli/memory_cli.py stm "The weather is nice today"

# Retrieve short-term memories
python cli/memory_cli.py get-stm

# Generate a prompt
python cli/memory_cli.py prompt -i "How is the project going?"
```

### REST API Server

```bash
# Run the API server
python api/memory_api.py
```

Web interface: http://localhost:5000

API Endpoints:
- GET `/api/v1/health` - Check status
- GET `/api/v1/blocks` - Retrieve block list
- POST `/api/v1/blocks` - Add a block
- GET `/api/v1/search?keywords=keyword1,keyword2` - Search by keywords
- GET, POST, DELETE `/api/v1/stm` - Manage short-term memory
- POST `/api/v1/prompt` - Generate prompts
- GET `/api/v1/verify` - Verify blockchain integrity

### Python Library

```python
from memory_engine import BlockManager, STMManager, CacheManager, PromptWrapper
from memory_engine.text_utils import process_user_input

# Process user input
user_input = "I started a new project and it's really exciting"
processed = process_user_input(user_input)

# Store memory with block manager
block_manager = BlockManager()
block = block_manager.add_block(
    context=processed["context"],
    keywords=processed["keywords"],
    tags=processed["tags"],
    embedding=processed["embedding"],
    importance=processed["importance"]
)

# Generate prompt
cache_manager = CacheManager(block_manager=block_manager)
prompt_wrapper = PromptWrapper(cache_manager=cache_manager)

user_question = "How is the project going?"
prompt = prompt_wrapper.compose_prompt(user_question)

# Pass to LLM
# llm_response = call_your_llm(prompt)
```

## 🧱 Architecture

```
memory-block-engine/
├── memory_engine/    # Core library
│   ├── block_manager.py    # Long-term memory management
│   ├── stm_manager.py      # Short-term memory management
│   ├── cache_manager.py    # Waypoint cache
│   ├── prompt_wrapper.py   # Prompt composition
│   ├── text_utils.py       # Text processing utilities
├── api/              # REST API interface
├── cli/              # Command-line tools
├── data/             # Data storage directory
```

## 📊 Memory Block Structure

```json
{
  "block_index": 143,
  "timestamp": "2025-05-08T01:02:33",
  "context": "I started a new project and it's really exciting",
  "keywords": ["project", "start", "exciting"],
  "tags": ["positive", "beginning", "motivated"],
  "embedding": [0.131, 0.847, ...],
  "importance": 0.91,
  "hash": "...",
  "prev_hash": "..."
}
```

## 🔧 Project Extensions

- **Embedding Improvements**: Integration with real embedding models (e.g., sentence-transformers)
- **Keyword Extraction Enhancement**: Implementation of language-specific keyword extraction
- **Cloud Integration**: Addition of database backends (SQLite, MongoDB, etc.)
- **Distributed Processing**: Implementation of distributed processing for large-scale memory management

## 📄 License

MIT License

## 👥 Contributing

We welcome all contributions including bug reports, feature suggestions, and pull requests!

## 📱 Contact

Email: playtart@play-t.art 
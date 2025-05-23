# 🧠 Greeum v0.5.2

<p align="center">
  <a href="../../README.md">🇰🇷 한국어</a> |
  <a href="README_EN.md">🇺�� English</a>
</p>

Multilingual LLM-independent Memory Management System

## 📌 Overview

**Greeum** (pronounced: gri-eum) is a **universal memory module** that can connect to any LLM (Large Language Model) and provides the following features:
- Long-term tracking of user utterances, goals, emotions, and intentions
- Recall of memories related to the current context
- Recognition and processing of temporal expressions in multilingual environments
- Functions as an "AI with memory"

The name "Greeum" is inspired by the Korean word "그리움" (longing/reminiscence), perfectly capturing the essence of the memory system.

Greeum is an LLM-independent memory system based on the RAG (Retrieval-Augmented Generation) architecture. It implements key components of RAG including information storage and retrieval (block_manager.py), related memory management (cache_manager.py), and prompt augmentation (prompt_wrapper.py) to generate more accurate and contextually relevant responses.

## 🔑 Key Features

- **Blockchain-like Long-Term Memory (LTM)**: Block-based memory storage with immutability
- **TTL-based Short-Term Memory (STM)**: Efficient management of temporarily important information
- **Semantic Relevance**: Keyword/tag/vector-based memory recall system
- **Waypoint Cache**: Automatic retrieval of memories related to the current context
- **Prompt Composer**: Automatic generation of LLM prompts with relevant memories
- **Temporal Reasoner**: Advanced temporal expression recognition in multilingual environments
- **Multilingual Support**: Automatic language detection and processing for Korean, English, etc.
- **Model Control Protocol**: External tool integration support for Cursor, Unity, Discord, etc. via separate [GreeumMCP](https://github.com/DryRainEnt/GreeumMCP) package

## ⚙️ Installation

1. Clone the repository
   ```bash
   git clone https://github.com/DryRainEnt/Greeum.git
   cd Greeum
   ```

2. Install dependencies
   ```bash
   pip install -r requirements.txt
   ```

## 🧪 Usage

### CLI Interface

```bash
# Add long-term memory
python cli/memory_cli.py add -c "Started a new project and it's really exciting"

# Search memories by keywords
python cli/memory_cli.py search -k "project,exciting"

# Search memories by temporal expression
python cli/memory_cli.py search-time -q "What did I do 3 days ago?" -l "en"

# Add short-term memory
python cli/memory_cli.py stm "The weather is nice today"

# Get short-term memories
python cli/memory_cli.py get-stm

# Generate prompt
python cli/memory_cli.py prompt -i "How is the project going?"
```

### REST API Server

```bash
# Run API server
python api/memory_api.py
```

Web interface: http://localhost:5000

API endpoints:
- GET `/api/v1/health` - Health check
- GET `/api/v1/blocks` - List blocks
- POST `/api/v1/blocks` - Add block
- GET `/api/v1/search?keywords=keyword1,keyword2` - Search by keywords
- GET `/api/v1/search/time?query=yesterday&language=en` - Search by temporal expression
- GET, POST, DELETE `/api/v1/stm` - Manage short-term memories
- POST `/api/v1/prompt` - Generate prompt
- GET `/api/v1/verify` - Verify blockchain integrity

### Python Library

```python
from greeum import BlockManager, STMManager, CacheManager, PromptWrapper
from greeum.text_utils import process_user_input
from greeum.temporal_reasoner import TemporalReasoner

# Process user input
user_input = "Started a new project and it's really exciting"
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

# Time-based search (multilingual)
temporal_reasoner = TemporalReasoner(db_manager=block_manager, default_language="auto")
time_query = "What did I do 3 days ago?"
time_results = temporal_reasoner.search_by_time_reference(time_query)

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
greeum/
├── greeum/                # Core library
│   ├── block_manager.py    # Long-term memory management
│   ├── stm_manager.py      # Short-term memory management
│   ├── cache_manager.py    # Waypoint cache
│   ├── prompt_wrapper.py   # Prompt composition
│   ├── text_utils.py       # Text processing utilities
│   ├── temporal_reasoner.py # Temporal reasoning
│   ├── embedding_models.py  # Embedding model integration
├── api/                   # REST API interface
├── cli/                   # Command-line tools
├── data/                  # Data storage directory
├── tests/                 # Test suite
```

## Branch Management Rules

- **main**: Stable release version branch
- **dev**: Core feature development branch (merged to main after development and testing)
- **test-collect**: Performance metrics and A/B test data collection branch

## 📊 Performance Tests

Greeum conducts performance tests in the following areas:

### T-GEN-001: Response Specificity Increase Rate
- Measurement of response quality improvement when using Greeum memory
- 18.6% average quality improvement confirmed
- 4.2 specific information inclusions increase

### T-MEM-002: Memory Search Latency
- Measurement of search speed improvement through waypoint cache
- 5.04x average speed improvement confirmed
- Up to 8.67x speed improvement for 1,000+ memory blocks

### T-API-001: API Call Efficiency
- Measurement of re-questioning reduction rate due to memory-based context provision
- 78.2% reduction in re-questioning necessity confirmed
- Cost reduction effect due to decreased API calls

## 📊 Memory Block Structure

```json
{
  "block_index": 143,
  "timestamp": "2025-05-08T01:02:33",
  "context": "Started a new project and it's really exciting",
  "keywords": ["project", "start", "exciting"],
  "tags": ["positive", "beginning", "motivation"],
  "embedding": [0.131, 0.847, ...],
  "importance": 0.91,
  "hash": "...",
  "prev_hash": "..."
}
```

## 🔤 Supported Languages

Greeum supports temporal expression recognition in the following languages:
- 🇰🇷 Korean: Basic support for Korean temporal expressions (어제, 지난주, 3일 전, etc.)
- 🇺🇸 English: Full support for English temporal formats (yesterday, 3 days ago, etc.)
- 🌐 Auto-detection: Automatically detects language and processes accordingly

## 🔍 Temporal Reasoning Examples

```python
# Korean
result = evaluate_temporal_query("3일 전에 뭐 했어?", language="ko")
# Return value: {detected: True, language: "ko", best_ref: {term: "3일 전"}}

# English
result = evaluate_temporal_query("What did I do 3 days ago?", language="en")
# Return value: {detected: True, language: "en", best_ref: {term: "3 days ago"}}

# Auto-detection
result = evaluate_temporal_query("What happened yesterday?")
# Return value: {detected: True, language: "en", best_ref: {term: "yesterday"}}
```

## 🔧 Project Expansion Plans

- **Model Control Protocol**: Check the [GreeumMCP](https://github.com/DryRainEnt/GreeumMCP) repository for MCP support - a separate package that allows Greeum to connect with tools like Cursor, Unity, Discord, etc.
- **Enhanced Multilingual Support**: Additional language support for Japanese, Chinese, Spanish, etc.
- **Improved Embeddings**: Integration of actual embedding models (e.g., sentence-transformers)
- **Enhanced Keyword Extraction**: Implementation of language-specific keyword extraction
- **Cloud Integration**: Addition of database backends (SQLite, MongoDB, etc.)
- **Distributed Processing**: Implementation of distributed processing for large-scale memory management

## 🌐 Website

Visit the website: [greeum.app](https://greeum.app)

## 📄 License

MIT License

## 👥 Contribution

All contributions are welcome, including bug reports, feature suggestions, pull requests, etc.!

## 📱 Contact

Email: playtart@play-t.art 
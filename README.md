#  Greeum v0.5.0

[![KR](https://img.shields.io/badge/README-?쒓뎅??blue.svg)](docs/i18n/README_KR.md)
[![EN](https://img.shields.io/badge/README-English-blue.svg)](README.md)
[![CN](https://img.shields.io/badge/README-訝?뻼-blue.svg)](docs/i18n/README_CN.md)
[![JP](https://img.shields.io/badge/README-?ζ쑍沃?blue.svg)](docs/i18n/README_JP.md)
[![ES](https://img.shields.io/badge/README-Espa챰ol-blue.svg)](docs/i18n/README_ES.md)

An LLM-Independent Memory System with Multilingual Support

## ?뱦 Overview

**Greeum** (pronounced as "gree-um") is a **universal memory module** that can be attached to any LLM model, designed to:
- Track user's long-term utterances, goals, emotions, and intentions
- Recall memories relevant to the current context
- Process temporal reasoning in multiple languages
- Function as an "AI with memory"

The name "Greeum" is inspired by the Korean word "洹몃━?" which evokes a sense of longing and remembrance - perfectly capturing the essence of a memory system.

## ?뵎 Key Features

- **Long-Term Memory Blocks**: Blockchain-like structure for immutable memory storage
- **Short-Term Memory Management**: TTL (Time-To-Live) structure for fluid temporary memories
- **Semantic Association**: Keyword/tag/vector-based memory recall system
- **Waypoint Cache**: Automatically retrieves memories related to the current context
- **Prompt Composition**: Automatic generation of LLM prompts that include relevant memories
- **Temporal Reasoning**: Advanced time expression recognition in multiple languages
- **Multilingual Support**: Automatic language detection and processing for Korean, English, and more
- **Model Control Protocol**: For MCP support, please check out [GreeumMCP](https://github.com/DryRainEnt/GreeumMCP) - a separate package that enables Greeum to connect with Cursor, Unity, Discord and other tools

## ?숋툘 Installation

1. Clone the repository
   ```bash
   git clone https://github.com/DryRainEnt/Greeum.git
   cd Greeum
   ```

2. Install dependencies
   ```bash
   # 湲곕낯 ?ㅼ튂
   pip install -r requirements.txt
   
   # PyPI?먯꽌 ?ㅼ튂
   pip install greeum
   
   # 紐⑤뱺 湲곕뒫 ?ы븿 ?ㅼ튂
   pip install greeum[all]
   ```

## ?㎦ Usage

### CLI Interface

```bash
# Add long-term memory
python cli/memory_cli.py add -c "I started a new project and it's really exciting"

# Search memories by keywords
python cli/memory_cli.py search -k "project,exciting"

# Search memories by time expression
python cli/memory_cli.py search-time -q "What did I do 3 days ago?" -l "auto"

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
- GET `/api/v1/search/time?query=yesterday&language=en` - Search by time expression
- GET, POST, DELETE `/api/v1/stm` - Manage short-term memory
- POST `/api/v1/prompt` - Generate prompts
- GET `/api/v1/verify` - Verify blockchain integrity

### Python Library

```python
from greeum import BlockManager, STMManager, CacheManager, PromptWrapper
from greeum.text_utils import process_user_input
from greeum.temporal_reasoner import TemporalReasoner

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

## ?㎟ Architecture

```
greeum/
?쒋?? greeum/                # Core library
??  ?쒋?? block_manager.py    # Long-term memory management
??  ?쒋?? stm_manager.py      # Short-term memory management
??  ?쒋?? cache_manager.py    # Waypoint cache
??  ?쒋?? prompt_wrapper.py   # Prompt composition
??  ?쒋?? text_utils.py       # Text processing utilities
??  ?쒋?? temporal_reasoner.py # Time-based reasoning 
??  ?쒋?? embedding_models.py  # Embedding model integration
?쒋?? api/                   # REST API interface
?쒋?? cli/                   # Command-line tools
?쒋?? memory_engine/         # Original memory engine implementation
?쒋?? data/                  # Data storage directory
?쒋?? tests/                 # Test suite
```

## Branch Management

- **main**: Stable release version branch
- **dev**: Core feature development branch (merged to main after testing)
- **test-collect**: Performance metrics and A/B test data collection branch

## ?뱤 Performance Tests

Greeum conducts performance tests in the following areas:

### T-GEN-001: Response Specificity Improvement Rate
- Measures response quality improvement when using Greeum memory
- Confirmed 18.6% average quality improvement
- Increase of 4.2 specific information points per response

### T-MEM-002: Memory Search Latency
- Measures speed improvement through waypoint cache
- Confirmed 5.04x average speed improvement
- Up to 8.67x speed improvement for 1,000+ memory blocks

### T-API-001: API Call Efficiency
- Measures reduction in follow-up questions due to memory-based context
- Confirmed 78.2% reduction in need for follow-up questions
- Cost savings from reduced API calls

## ?뱤 Memory Block Structure

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

## ?뵥 Supported Languages

Greeum supports time expression recognition in the following languages:
- ?눖?눟 Korean: Native support for Korean time expressions (?댁젣, 吏?쒖＜, 3???? etc.)
- ?눣?눡 English: Full support for English time formats (yesterday, 3 days ago, etc.)
- ?뙋 Auto-detection: Automatically detects the language and processes accordingly

## ?뵇 Temporal Reasoning Examples

```python
# Korean
result = evaluate_temporal_query("3???꾩뿉 萸??덉뼱?", language="ko")
# Returns: {detected: True, language: "ko", best_ref: {term: "3????}}

# English
result = evaluate_temporal_query("What did I do 3 days ago?", language="en")
# Returns: {detected: True, language: "en", best_ref: {term: "3 days ago"}}

# Auto-detection
result = evaluate_temporal_query("What happened yesterday?")
# Returns: {detected: True, language: "en", best_ref: {term: "yesterday"}}
```

## ?뵩 Project Extensions

- **Enhanced Multilingual Support**: Expanding to Japanese, Chinese, Spanish and more languages
- **Embedding Improvements**: Integration with real embedding models (e.g., sentence-transformers)
- **Keyword Extraction Enhancement**: Implementation of language-specific keyword extraction
- **Cloud Integration**: Addition of database backends (SQLite, MongoDB, etc.)
- **Distributed Processing**: Implementation of distributed processing for large-scale memory management
- **Tool Integrations**: See [GreeumMCP](https://github.com/DryRainEnt/GreeumMCP) for Model Control Protocol support

## ?뙋 Website

Visit our website: [greeum.app](https://greeum.app)

## ?뱞 License

MIT License

## ?뫁 Contributing

We welcome all contributions including bug reports, feature suggestions, and pull requests!

## ?벑 Contact

Email: playtart@play-t.art 

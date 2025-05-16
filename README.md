# 🧠 Greeum v0.4.0

[![KR](https://img.shields.io/badge/README-한국어-blue.svg)](docs/i18n/README_KR.md)
[![EN](https://img.shields.io/badge/README-English-blue.svg)](README.md)
[![CN](https://img.shields.io/badge/README-中文-blue.svg)](docs/i18n/README_CN.md)
[![JP](https://img.shields.io/badge/README-日本語-blue.svg)](docs/i18n/README_JP.md)
[![ES](https://img.shields.io/badge/README-Español-blue.svg)](docs/i18n/README_ES.md)

An LLM-Independent Memory System with Multilingual Support

## 📌 Overview

**Greeum** (pronounced as "gree-um") is a **universal memory module** that can be attached to any LLM model, designed to:
- Track user's long-term utterances, goals, emotions, and intentions
- Recall memories relevant to the current context
- Process temporal reasoning in multiple languages
- Function as an "AI with memory"

The name "Greeum" is inspired by the Korean word "그리움" which evokes a sense of longing and remembrance - perfectly capturing the essence of a memory system.

## 🔑 Key Features

- **Long-Term Memory Blocks**: Blockchain-like structure for immutable memory storage
- **Short-Term Memory Management**: TTL (Time-To-Live) structure for fluid temporary memories
- **Semantic Association**: Keyword/tag/vector-based memory recall system
- **Waypoint Cache**: Automatically retrieves memories related to the current context
- **Prompt Composition**: Automatic generation of LLM prompts that include relevant memories
- **Temporal Reasoning**: Advanced time expression recognition in multiple languages
- **Multilingual Support**: Automatic language detection and processing for Korean, English, and more
- **MCP Integration**: Model Control Protocol support for connecting with Cursor, Unity, Discord and other tools

## ⚙️ Installation

1. Clone the repository
   ```bash
   git clone https://github.com/DryRainEnt/Greeum.git
   cd Greeum
   ```

2. Install dependencies
   ```bash
   # 기본 설치
   pip install -r requirements.txt
   
   # PyPI에서 설치
   pip install greeum
   
   # MCP 기능 포함 설치
   pip install greeum[mcp]
   
   # 모든 기능 포함 설치
   pip install greeum[all]
   ```

## 🧪 Usage

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

### MCP (Model Control Protocol) Integration

#### 설치 및 설정

```bash
# MCP 기능 포함 설치
pip install greeum[mcp]

# 환경 변수 설정 (선택 사항)
export ADMIN_KEY="your_admin_secret_key"  # API 키 관리를 위한 관리자 키
```

#### MCP 서비스 실행

```bash
# CLI 명령을 통한 서비스 실행
greeum-mcp --port 8000 --data-dir ./data

# 또는 Python 모듈로 직접 실행
python -m memory_engine.mcp_service --port 8000 --data-dir ./data
```

#### MCP 클라이언트 사용 예제

```python
# MCP 클라이언트 사용
from memory_engine.mcp_client import MCPClient

# 클라이언트 초기화 (API 키 필요)
client = MCPClient(api_key="YOUR_API_KEY")

# 기억 추가
result = client.manage_memory(
    action="add",
    memory_content="This is a memory created through MCP interface"
)

# 기억 검색
memories = client.manage_memory(
    action="query",
    query="MCP",
    limit=5
)

# Unity 통합 예제 (Unity가 MCP 호환되어 있는 경우)
result = client.execute_menu_item(menu_path="GameObject/Create Empty")
```

#### MCP 기능으로 할 수 있는 것들

- 외부 도구와 Greeum 기억 시스템 연동
- 장기/단기 기억 관리 API 호출
- API 키 기반 인증
- 실시간 기억 검색 및 저장

더 자세한 MCP 사용 방법은 `examples/README.md`를 참조하세요.

## 🧱 Architecture

```
greeum/
├── greeum/                # Core library
│   ├── block_manager.py    # Long-term memory management
│   ├── stm_manager.py      # Short-term memory management
│   ├── cache_manager.py    # Waypoint cache
│   ├── prompt_wrapper.py   # Prompt composition
│   ├── text_utils.py       # Text processing utilities
│   ├── temporal_reasoner.py # Time-based reasoning 
│   ├── embedding_models.py  # Embedding model integration
├── api/                   # REST API interface
├── cli/                   # Command-line tools
├── memory_engine/         # Original memory engine implementation
│   ├── mcp_client.py       # MCP client implementation
│   ├── mcp_service.py      # MCP service implementation
│   ├── mcp_integrations.py # MCP integration utilities
├── data/                  # Data storage directory
├── examples/              # Usage examples
├── tests/                 # Test suite
```

## Branch Management

- **main**: Stable release version branch
- **dev**: Core feature development branch (merged to main after testing)
- **test-collect**: Performance metrics and A/B test data collection branch

## 📊 Performance Tests

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

## 🔤 Supported Languages

Greeum supports time expression recognition in the following languages:
- 🇰🇷 Korean: Native support for Korean time expressions (어제, 지난주, 3일 전, etc.)
- 🇺🇸 English: Full support for English time formats (yesterday, 3 days ago, etc.)
- 🌐 Auto-detection: Automatically detects the language and processes accordingly

## 🔍 Temporal Reasoning Examples

```python
# Korean
result = evaluate_temporal_query("3일 전에 뭐 했어?", language="ko")
# Returns: {detected: True, language: "ko", best_ref: {term: "3일 전"}}

# English
result = evaluate_temporal_query("What did I do 3 days ago?", language="en")
# Returns: {detected: True, language: "en", best_ref: {term: "3 days ago"}}

# Auto-detection
result = evaluate_temporal_query("What happened yesterday?")
# Returns: {detected: True, language: "en", best_ref: {term: "yesterday"}}
```

## 🔧 Project Extensions

- **Enhanced Multilingual Support**: Expanding to Japanese, Chinese, Spanish and more languages
- **Embedding Improvements**: Integration with real embedding models (e.g., sentence-transformers)
- **Keyword Extraction Enhancement**: Implementation of language-specific keyword extraction
- **Cloud Integration**: Addition of database backends (SQLite, MongoDB, etc.)
- **Distributed Processing**: Implementation of distributed processing for large-scale memory management
- **Tool Integrations**: Expanded MCP support for additional tools and platforms

## 🌐 Website

Visit our website: [greeum.app](https://greeum.app)

## 📄 License

MIT License

## 👥 Contributing

We welcome all contributions including bug reports, feature suggestions, and pull requests!

## 📱 Contact

Email: playtart@play-t.art 
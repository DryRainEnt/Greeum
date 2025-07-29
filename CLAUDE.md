# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Greeum** (pronounced "그리음") is a universal memory module for Large Language Models (LLMs) that provides human-like memory capabilities. It's designed to be LLM-agnostic and supports multiple languages, particularly Korean and English.

### Core Architecture

The system follows a RAG (Retrieval-Augmented Generation) architecture with these main components:

- **BlockManager**: Long-term memory storage using blockchain-like immutable blocks
- **STMManager**: Short-term memory with TTL-based cache management  
- **CacheManager**: Waypoint cache for context-relevant memory retrieval
- **PromptWrapper**: Automatic prompt composition with relevant memories
- **TemporalReasoner**: Multi-language temporal expression processing
- **SearchEngine**: FAISS vector indexing with BERT cross-encoder reranking
- **MemoryEvolutionManager**: Memory summarization and conflict resolution

## Development Commands

### Testing
```bash
# Run tests with tox (supports Python 3.10, 3.11, 3.12)
tox

# Run specific Python version tests
tox -e py312

# Run benchmark tests  
tox -e bench

# Run performance smoke test
python scripts/bench_smoke.py --quick
```

### Installation & Setup
```bash
# Install basic dependencies
pip install -r requirements.txt

# Install with all optional dependencies (recommended)
pip install greeum[all]  # includes faiss, transformers, keybert, openai

# Install for development
pip install -e .
```

### Running the Application

#### CLI Interface
```bash
# Add long-term memory
python cli/memory_cli.py add -c "새로운 프로젝트를 시작했고 정말 흥미로워요"

# Search by keywords
python cli/memory_cli.py search -k "프로젝트,흥미로운"

# Search by temporal expressions (multilingual)
python cli/memory_cli.py search-time -q "3일 전에 무엇을 했지?" -l "ko"

# Manage short-term memory
python cli/memory_cli.py stm "오늘 날씨가 좋네요"
python cli/memory_cli.py get-stm

# Generate enhanced prompts
python cli/memory_cli.py prompt -i "프로젝트는 어떻게 진행되고 있나요?"
```

#### REST API Server
```bash
# Start API server
python api/memory_api.py

# Server runs on http://localhost:5000
# Web interface available at the same URL
```

## Code Architecture

### Core Memory System
```
greeum/
├── block_manager.py      # Long-term memory blocks (immutable, blockchain-like)
├── stm_manager.py        # Short-term memory with TTL
├── cache_manager.py      # Waypoint cache for context relevance
├── prompt_wrapper.py     # LLM prompt composition
├── database_manager.py   # SQLite/PostgreSQL database abstraction
├── vector_index.py       # FAISS vector indexing
├── search_engine.py      # Advanced search with BERT reranking
├── temporal_reasoner.py  # Multilingual time expression processing
├── text_utils.py         # Text processing utilities
├── embedding_models.py   # Multiple embedding model support
├── memory_evolution.py   # Memory summarization and evolution
└── knowledge_graph.py    # Knowledge graph management
```

### Interface Layers
```
api/           # Flask REST API with Swagger documentation
cli/           # Command-line interface
examples/      # Usage examples and client demos
```

### Memory Block Structure
Each memory block follows this JSON schema:
```json
{
  "block_index": 143,
  "timestamp": "2025-05-08T01:02:33",
  "context": "새로운 프로젝트를 시작했고 정말 흥미로워요",
  "keywords": ["프로젝트", "시작", "흥미로운"],
  "tags": ["긍정적", "시작", "동기부여"],
  "embedding": [0.131, 0.847, ...],
  "importance": 0.91,
  "hash": "...",
  "prev_hash": "..."
}
```

## Key Features to Understand

### 1. Multilingual Support
- Automatic language detection for Korean/English
- Temporal expression processing in multiple languages
- Example: "3일 전에 뭐 했어?" vs "What did I do 3 days ago?"

### 2. Memory Evolution
- Automatic memory block summarization
- Conflict detection and resolution
- Long-term memory optimization

### 3. Advanced Search
- FAISS vector similarity search
- BERT cross-encoder reranking
- Keyword + semantic + temporal search combination

### 4. Multiple Embedding Models
- Simple embedding (hash-based)
- Sentence-BERT transformers
- OpenAI embeddings
- Pluggable embedding registry system

## Development Patterns

### Adding New Features
1. Core logic goes in `greeum/` modules
2. Add corresponding tests in `tests/`
3. Update CLI commands in `cli/memory_cli.py`
4. Add REST API endpoints in `api/memory_api.py`
5. Update examples in `examples/`

### Testing Guidelines
- Use `unittest` framework (not pytest currently configured)
- Tests are in `tests/` directory
- Performance tests use custom benchmark system in `scripts/`
- Mock external dependencies (OpenAI API, FAISS) in tests

### Import Patterns
```python
# Core imports
from greeum import BlockManager, STMManager, CacheManager, PromptWrapper
from greeum.text_utils import process_user_input
from greeum.temporal_reasoner import TemporalReasoner

# Client usage
from greeum.client import MemoryClient, SimplifiedMemoryClient
```

### Database Configuration
- Default: SQLite in `data/` directory
- Production: PostgreSQL support via SQLAlchemy
- Vector storage: FAISS indexes for similarity search

## Performance Considerations

The system has been benchmarked with these metrics:
- **T-GEN-001**: 18.6% average response quality improvement
- **T-MEM-002**: 5.04x average search speed improvement with waypoint cache
- **T-API-001**: 78.2% reduction in re-questioning needs

Key performance files:
- `results/` directory contains benchmark data and visualizations
- `tests/performance_metrics.py` for performance testing utilities

## Configuration

### Environment Variables
The system reads configuration from:
- Environment variables
- `.env` files
- Direct parameter passing

### Data Storage
- `data/block_memory.jsonl` - Block storage (legacy)
- `data/short_term.json` - STM storage
- `data/context_cache.json` - Waypoint cache
- SQLite database for structured storage (newer approach)

## API Integration

The system provides both REST API and Python client interfaces:
- REST API uses Flask-RESTX with Swagger documentation
- Python client with retry logic and error handling
- MCP (Model Control Protocol) support via separate GreeumMCP package

## Internationalization

Documentation available in multiple languages:
- Korean (main): `README.md`
- English: `docs/i18n/README_EN.md`
- Chinese, Japanese, Spanish, German, French versions available
# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## ⚠️ CRITICAL REQUIREMENTS (v3.1.1a1+)

### Semantic Embedding Requirement
**MANDATORY**: The system requires proper semantic embeddings for core functionality.

**Problem**: Without sentence-transformers or equivalent semantic embedding models:
- All similarities compute to ~0 (using hash-based random embeddings)
- Slot selection degrades to meaningless round-robin
- The 0.4 similarity threshold becomes ineffective
- Context-aware memory grouping fails completely
- Branch-based indexing provides no value

**Solution**: Install semantic embedding support:
```bash
# Option 1: Install with full dependencies (RECOMMENDED)
pip install greeum[full]

# Option 2: Install sentence-transformers separately
pip install sentence-transformers

# Verify installation:
python -c "from sentence_transformers import SentenceTransformer; print('✓ Ready')"
```

**Version History**:
- v3.1.0: FAILED - Discovered using random hash embeddings
- v3.1.1a1: Target - Proper semantic embeddings implementation

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

#### CLI Interface (v2.2.5+)
```bash
# Add long-term memory
greeum memory add "새로운 프로젝트를 시작했고 정말 흥미로워요"

# Search memories
greeum memory search "프로젝트 흥미로운" --count 5

# Memory Anchors (NEW in v2.2.5)
greeum anchors status                    # View anchor status
greeum anchors set A 123                # Pin memory #123 to slot A
greeum anchors pin A                     # Prevent auto-movement
greeum memory search "query" --slot A   # Search near anchor A

# Get recent memories
greeum recent-memories --count 10

# Initialize memory engine
greeum init --db-path data/memory.db
```

#### REST API Server
```bash
# Note: REST API server is available but requires separate setup
# Refer to MCP integration for modern usage with Claude Code
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

## Claude Code MCP Integration

### Setting up GreeumMCP with Claude Code

**Prerequisites:**
- Greeum v2.5.0+ installed (includes anchored memory system)
- Claude Desktop application

#### Step 1: Install Dependencies
```bash
# Install core packages (latest version with anchors)
pip install greeum>=2.2.5
pip install greeummcp>=1.0.0

# Install required dependencies for MCP server
pip install numpy>=1.24.0
```

#### Step 2: Configure Claude Desktop
Edit `~/Library/Application Support/Claude/claude_desktop_config.json` (macOS), `~/.config/claude-desktop/claude_desktop_config.json` (Linux), or `%APPDATA%\Claude\claude_desktop_config.json` (Windows):

```json
{
  "mcpServers": {
    "greeum_mcp": {
      "command": "python3",
      "args": [
        "/path/to/GreeumMCP/minimal_mcp_server.py"
      ],
      "env": {
        "GREEUM_LOG_LEVEL": "INFO",
        "PYTHONPATH": "/path/to/Greeum:/path/to/GreeumMCP"
      }
    }
  }
}
```

**Note**: GREEUM_DATA_DIR is optional. Without it, Greeum will automatically use:
- Project local: `./data/memory.db` (when in project directory)
- User home: `~/.greeum/memory.db` (as fallback)

#### Step 3: Create MCP Server Script
Ensure your GreeumMCP installation includes `minimal_mcp_server.py` or `working_mcp_server.py`:

```python
# Example minimal_mcp_server.py structure
import asyncio
import json
from mcp.server import Server
from greeum import BlockManager, DatabaseManager

async def main():
    server = Server("greeum-memory")
    
    # Initialize Greeum components
    db_manager = DatabaseManager()
    block_manager = BlockManager(db_manager)
    
    # Define MCP tools
    @server.list_tools()
    async def list_tools():
        return [
            {"name": "add_memory", "description": "Add memory to Greeum"},
            {"name": "search_memory", "description": "Search Greeum memories"}
        ]
    
    # Run server
    await server.run()

if __name__ == "__main__":
    asyncio.run(main())
```

#### Step 4: Verify Connection
```bash
# Check MCP server status
claude mcp list

# Should show:
# greeum_mcp: python3 /path/to/minimal_mcp_server.py - ✓ Connected
```

#### Step 5: Test MCP Functions
In Claude Code, you can now use:
- `add_memory(content, importance=0.5)` - Add new memory blocks
- `search_memory(query, limit=5)` - Search existing memories
- `get_memory_stats()` - View memory system statistics
- `usage_analytics(days=7)` - Get usage analytics and insights

**Note**: Anchor management is available through CLI only. Use `greeum anchors` commands in terminal for anchor operations.

### Troubleshooting

**Common Issues:**

1. **"Failed to connect" error:**
   - Verify PYTHONPATH includes both Greeum and GreeumMCP directories
   - Check that numpy is installed in the Python environment
   - Ensure file paths are absolute, not relative

2. **Import errors:**
   - Install missing dependencies: `pip install numpy mcp`
   - Verify Greeum v1.0.0+ is properly installed
   - Check Python version compatibility (3.10+)

3. **Permission errors:**
   - Ensure data directory is writable
   - Check file permissions on MCP server script

**Successful Configuration Indicators:**
- `claude mcp list` shows "✓ Connected"
- MCP tools appear in Claude Code interface
- Memory operations work without errors

This setup enables seamless integration between Claude Code and Greeum's memory system, allowing persistent context across conversations.

## Greeum 메모리 사용 원칙 (그레마스 액탄트 모델 기반)

### 저장 단위: 액션 단위 라벨링
모든 메모리 저장은 그레마스 6개 액탄트 역할을 기반으로 [주체-행동-객체] 구조의 1-2문장으로 기록:

**저장 패턴 예시:**
- `[사용자-요청-MCP도구테스트] 연결된 도구 파악 및 테스트 진행`
- `[Claude-발견-TypeScript오류] src/types/session.ts의 processId 타입 불일치`
- `[팀-결정-아키텍처변경] 마이크로서비스에서 모놀리스로 전환, 성능상 이유`
- `[사용자-제안-그레마스모델적용] 액탄트 구조로 상호작용 패턴 기록`

### 저장 빈도: 모든 상호작용은 영구 보존 가치
**기본 원칙**: "모든 작업 단위는 영구 보존 가치가 있다" - 중요도 판단보다 패턴 누적 우선

**저장 시점:**
- ✅ 사용자 질문/요청마다 저장
- ✅ 도구 사용 결과마다 저장  
- ✅ 문제 발견/해결마다 저장
- ✅ 작업 전환점마다 저장
- ✅ 피드백과 개선사항마다 저장
- ✅ 코드 변경, 설정 수정마다 저장
- ✅ 테스트 결과, 성능 측정마다 저장

### 실제 적용 패턴
현재 대화 기준 권장 저장 패턴:
```
[사용자-질문-MCP도구파악] → 즉시 저장
[Claude-테스트-Greeum기능4개] → 즉시 저장  
[사용자-질문-사용빈도분석] → 즉시 저장
[Claude-분석-Description vs CLAUDE.md차이] → 즉시 저장
[사용자-요청-메모리조회] → 즉시 저장
[사용자-제안-그레마스모델적용] → 즉시 저장
```

### 목표 메트릭
- **세션당 블록 수**: 20-30개 (촘촘한 기록)
- **저장 빈도**: 3-5분마다 최소 1회  
- **패턴 누적**: 반복 작업도 미묘한 차이점 포착하여 학습 효과 극대화

이 방식으로 Greeum은 진정한 **외부 두뇌(Extended Mind)** 역할을 수행할 수 있습니다.

## Internationalization

Documentation available in multiple languages:
- Korean (main): `README.md`
- English: `docs/i18n/README_EN.md`
- Chinese, Japanese, Spanish, German, French versions available
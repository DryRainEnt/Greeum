# Greeum API Reference

Complete API documentation for Greeum v2.2.5a1. This guide covers all classes, methods, and integration patterns for building advanced memory systems with anchor-based exploration.

## Table of Contents

### Core Components
- [BlockManager](#blockmanager) - Long-term memory management
- [STMManager](#stmmanager) - Short-term memory management  
- [CacheManager](#cachemanager) - Waypoint cache system
- [PromptWrapper](#promptwrapper) - Enhanced prompt composition
- [DatabaseManager](#databasemanager) - Database operations

### Anchor System (v2.2+)
- [AnchorManager](#anchormanager) - 3-slot STM anchor management
- [GraphIndex](#graphindex) - Graph-based memory traversal
- [SearchEngine](#searchengine) - Anchor-aware search with localized exploration
- [AnchorBasedWriter](#anchorbasedwriter) - Near-anchor block placement
- [AutoAnchorMovement](#autoanchormovement) - Intelligent anchor optimization

### Advanced Features
- [QualityValidator](#qualityvalidator) - Memory quality assessment
- [DuplicateDetector](#duplicatedetector) - Duplicate prevention
- [UsageAnalytics](#usageanalytics) - Usage pattern analysis
- [TemporalReasoner](#temporalreasoner) - Time-based reasoning
- [LTMLinksCache](#ltmlinkscache) - Neighbor relationship caching

### MCP Integration
- [MCP Tools](#mcp-tools) - 12 MCP tools for Claude Code
- [MCP Server](#mcp-server) - Server configuration and usage

### CLI & REST API
- [CLI Commands](#cli-commands) - Command-line interface
- [REST Endpoints](#rest-endpoints) - HTTP API endpoints

### Utilities
- [Embedding Models](#embedding-models) - Vector generation
- [Text Utils](#text-utils) - Text processing utilities

---

## Core Components

### BlockManager

Manages long-term memory blocks with blockchain-like immutable structure.

#### `__init__(db_manager=None)`

Initialize BlockManager with optional database manager.

```python
from greeum import BlockManager, DatabaseManager

# Use default SQLite database
bm = BlockManager()

# Use custom database manager
db_manager = DatabaseManager("custom_path/memory.db")
bm = BlockManager(db_manager)
```

#### `add_block(context, keywords, tags, embedding, importance, metadata=None)`

Add a new memory block to long-term storage.

**Parameters:**
- `context` (str): Memory content
- `keywords` (List[str]): Associated keywords
- `tags` (List[str]): Associated tags  
- `embedding` (List[float]): Vector embedding
- `importance` (float): Importance score (0.0-1.0)
- `metadata` (Dict, optional): Additional metadata

**Returns:** `Dict[str, Any]` - Created block data

```python
block = bm.add_block(
    context="Attended team meeting about Q4 goals",
    keywords=["meeting", "goals", "team"],
    tags=["work", "planning"],
    embedding=get_embedding("meeting content"),
    importance=0.8,
    metadata={"meeting_id": "mt_001", "participants": 5}
)
```

#### `search_by_keywords(keywords, limit=10)`

Search blocks by keywords.

```python
results = bm.search_by_keywords(["python", "project"], limit=5)
```

#### `search_by_embedding(query_embedding, top_k=5)`

Search blocks by vector similarity.

```python
from greeum.embedding_models import get_embedding

query_emb = get_embedding("What did we discuss about the project?")
similar_blocks = bm.search_by_embedding(query_emb, top_k=10)
```

#### `get_blocks(limit=None, sort_by='timestamp', order='desc')`

Retrieve blocks with sorting options.

```python
# Get recent blocks
recent = bm.get_blocks(limit=10)

# Get by importance
important = bm.get_blocks(limit=20, sort_by='importance', order='desc')
```

#### `verify_blocks()`

Verify blockchain integrity of all blocks.

```python
is_valid = bm.verify_blocks()
if not is_valid:
    print("Blockchain integrity compromised!")
```

### STMManager

Manages short-term memory with TTL-based expiration.

#### `__init__(db_manager=None, default_ttl=3600)`

Initialize STM manager with TTL settings.

```python
from greeum import STMManager

# 1-hour default TTL
stm = STMManager(default_ttl=3600)

# 30-minute TTL
stm = STMManager(default_ttl=1800)
```

#### `add_memory(memory_data, ttl=None)`

Add short-term memory with optional custom TTL.

```python
memory = {
    "id": "stm_001",
    "content": "User is working on Python FastAPI project",
    "speaker": "user",
    "importance": 0.7
}

stm.add_memory(memory, ttl=7200)  # 2-hour TTL
```

#### `get_recent_memories(count=5, include_expired=False)`

Retrieve recent short-term memories.

```python
recent_memories = stm.get_recent_memories(count=10)
all_memories = stm.get_recent_memories(count=20, include_expired=True)
```

#### `cleanup_expired()`

Remove expired short-term memories.

```python
removed_count = stm.cleanup_expired()
print(f"Removed {removed_count} expired memories")
```

### CacheManager

Manages waypoint cache for context-relevant memory retrieval.

#### `__init__(block_manager=None, stm_manager=None, max_cache_size=50)`

Initialize cache manager with memory managers.

```python
from greeum import CacheManager, BlockManager, STMManager

bm = BlockManager()
stm = STMManager()
cache = CacheManager(bm, stm, max_cache_size=100)
```

#### `update_cache(query_text, query_embedding, query_keywords)`

Update cache based on current query context.

```python
from greeum.embedding_models import get_embedding
from greeum.text_utils import extract_keywords

query = "What did we decide about the new features?"
embedding = get_embedding(query)
keywords = extract_keywords(query)

cache.update_cache(query, embedding, keywords)
```

#### `get_relevant_memories(limit=10)`

Get cached memories relevant to current context.

```python
relevant = cache.get_relevant_memories(limit=15)
```

### PromptWrapper

Composes enhanced prompts with relevant memories.

#### `__init__(cache_manager=None, stm_manager=None)`

Initialize prompt wrapper with memory managers.

```python
from greeum import PromptWrapper, CacheManager, STMManager

cache = CacheManager()
stm = STMManager()
wrapper = PromptWrapper(cache, stm)
```

#### `compose_prompt(user_input, include_stm=True, max_context_length=2000)`

Generate enhanced prompt with memory context.

```python
user_query = "How should we approach the database design?"
enhanced_prompt = wrapper.compose_prompt(
    user_query, 
    include_stm=True,
    max_context_length=3000
)
```

### DatabaseManager

Low-level database operations for memory storage.

#### `__init__(connection_string=None, db_type='sqlite')`

Initialize database connection.

```python
from greeum.core import DatabaseManager

# SQLite (default)
db = DatabaseManager("data/custom.db")

# PostgreSQL
db = DatabaseManager(
    "postgresql://user:pass@localhost/greeum",
    db_type='postgres'
)
```

#### Database Operations

```python
# Store block
block_data = {...}
db.store_block(block_data)

# Get block
block = db.get_block(42)

# Search operations
results = db.search_blocks_by_keyword(["python", "api"])
similar = db.search_blocks_by_embedding(embedding_vector)
```

---

## Advanced Features (v2.0.5)

### QualityValidator

Automatic memory quality assessment with 7-factor analysis.

#### `__init__()`

Initialize quality validator.

```python
from greeum.core.quality_validator import QualityValidator

validator = QualityValidator()
```

#### `validate_memory_quality(content, importance=0.5, context=None)`

Assess memory quality with detailed metrics.

```python
result = validator.validate_memory_quality(
    content="Attended team meeting about Q4 roadmap and resource allocation",
    importance=0.8
)

print(f"Quality Score: {result['quality_score']:.3f}")
print(f"Quality Level: {result['quality_level']}")
print(f"Factors: {result['quality_factors']}")
print(f"Suggestions: {result['suggestions']}")
```

**Quality Factors:**
1. **Length**: Appropriate information volume
2. **Richness**: Meaningful word ratio and lexical diversity
3. **Structure**: Sentence and paragraph composition
4. **Language**: Grammar and expression quality
5. **Information Density**: Specific information content
6. **Searchability**: Future search convenience
7. **Temporal Relevance**: Current context relevance

### DuplicateDetector

Intelligent duplicate memory detection with 85% similarity threshold.

#### `__init__(db_manager=None, similarity_threshold=0.85)`

Initialize duplicate detector.

```python
from greeum.core.duplicate_detector import DuplicateDetector

detector = DuplicateDetector(similarity_threshold=0.90)
```

#### `check_duplicates(content, embedding=None, top_k=5)`

Check for duplicate memories.

```python
result = detector.check_duplicates(
    content="Meeting about project timeline",
    embedding=content_embedding
)

if result['is_duplicate']:
    print(f"Found {len(result['similar_memories'])} similar memories")
    print(f"Highest similarity: {result['max_similarity']:.3f}")
```

### UsageAnalytics

Comprehensive usage pattern analysis and monitoring.

#### `__init__(db_manager=None, analytics_db_path=None)`

Initialize usage analytics system.

```python
from greeum.core.usage_analytics import UsageAnalytics

analytics = UsageAnalytics()
```

#### `log_event(event_type, tool_name=None, metadata=None, duration_ms=None, success=True)`

Log usage events for analysis.

```python
analytics.log_event(
    event_type="tool_usage",
    tool_name="add_memory",
    metadata={"quality_score": 0.85, "importance": 0.7},
    duration_ms=150,
    success=True
)
```

#### `get_usage_statistics(days=7, user_id=None)`

Get comprehensive usage statistics.

```python
stats = analytics.get_usage_statistics(days=30)

print(f"Total events: {stats['total_events']}")
print(f"Unique sessions: {stats['unique_sessions']}")
print(f"Average response time: {stats['avg_response_time']:.0f}ms")
print(f"Success rate: {stats['success_rate']*100:.1f}%")
```

#### `get_quality_trends(days=7)`

Analyze memory quality trends over time.

```python
trends = analytics.get_quality_trends(days=30)

print(f"Average quality: {trends['avg_quality_score']:.3f}")
print(f"High quality ratio: {trends['high_quality_ratio']*100:.1f}%")
```

### TemporalReasoner

Process temporal expressions in multiple languages.

#### `__init__(db_manager=None)`

Initialize temporal reasoner.

```python
from greeum import TemporalReasoner

reasoner = TemporalReasoner()
```

#### `search_by_time(query, language='auto', top_k=10)`

Search memories by temporal expressions.

```python
# English
results = reasoner.search_by_time("What did I do 3 days ago?", language='en')

# Korean  
results = reasoner.search_by_time("지난 주에 무엇을 했지?", language='ko')

# Auto-detect
results = reasoner.search_by_time("昨日何をしましたか？")
```

### SearchEngine

Advanced search with optional BERT reranking.

#### `__init__(block_manager=None, reranker=None)`

Initialize search engine with optional reranker.

```python
from greeum.core.search_engine import SearchEngine, BertReranker

# Basic search
engine = SearchEngine()

# With BERT reranking
reranker = BertReranker("cross-encoder/ms-marco-MiniLM-L-6-v2")
engine = SearchEngine(reranker=reranker)
```

#### `search(query, top_k=5, slot=None, radius=2, fallback=True)`

Perform advanced search with optional anchor-based localized exploration.

```python
# Basic search (no anchors)
results = engine.search("project planning meeting", top_k=10)

# Anchor-based localized search
results = engine.search(
    query="API authentication",
    top_k=5,
    slot='A',           # Use anchor slot A
    radius=2,           # Search within 2-hop radius
    fallback=True       # Fall back to global search if needed
)

print(f"Found {len(results['blocks'])} results")
print(f"Search time: {results['metadata']['search_time_ms']:.0f}ms")
print(f"Used local search: {results['metadata'].get('local_search_used', False)}")
```

**Parameters:**
- `query` (str): Search query text
- `top_k` (int): Maximum number of results to return  
- `slot` (str, optional): Anchor slot to use ('A', 'B', or 'C')
- `radius` (int): Number of hops for localized search (default: 2)
- `fallback` (bool): Whether to use global search if local fails (default: True)

---

## Anchor System (v2.2+)

### AnchorManager

Manages 3-slot STM anchor state for context-aware memory exploration.

#### `__init__(store_path)`

Initialize anchor manager with persistent storage.

```python
from greeum.anchors.manager import AnchorManager
from pathlib import Path

anchor_manager = AnchorManager(Path("data/anchors.json"))
```

#### `get_slot_info(slot)`

Get information about a specific anchor slot.

```python
slot_info = anchor_manager.get_slot_info('A')
if slot_info:
    print(f"Anchor block: {slot_info['anchor_block_id']}")
    print(f"Summary: {slot_info['summary']}")
    print(f"Hop budget: {slot_info.get('hop_budget', 3)}")
    print(f"Pinned: {slot_info.get('pinned', False)}")
```

#### `move_anchor(slot, new_block_id, topic_vec, summary, hop_budget=3)`

Move anchor to a new block with context.

```python
success = anchor_manager.move_anchor(
    slot='A',
    new_block_id='12345',
    topic_vec=[0.1, 0.2, ...],  # 128-dim embedding
    summary="API development discussion",
    hop_budget=2
)
```

#### `pin_anchor(slot)` / `unpin_anchor(slot)`

Pin or unpin anchor to prevent/allow automatic movement.

```python
# Prevent automatic movement
anchor_manager.pin_anchor('A')

# Allow automatic movement
anchor_manager.unpin_anchor('A')
```

### GraphIndex

Lightweight graph structure for memory block relationships.

#### `__init__(theta=0.4, kmax=16)`

Initialize graph index with similarity threshold and max connections.

```python
from greeum.graph.index import GraphIndex

graph = GraphIndex(theta=0.4, kmax=16)
```

#### `upsert_edges(block_id, neighbors)`

Add or update edges for a block.

```python
# Add edges with weights
neighbors = [("block_123", 0.8), ("block_456", 0.6)]
graph.upsert_edges("block_789", neighbors)
```

#### `neighbors(block_id, k=5)`

Get k nearest neighbors of a block.

```python
neighbors = graph.neighbors("block_789", k=3)
for neighbor_id, weight in neighbors:
    print(f"Neighbor: {neighbor_id}, weight: {weight:.3f}")
```

### AnchorBasedWriter

Writer that places new blocks near anchor neighborhoods.

#### `__init__(db_manager=None, anchor_path=None, graph_path=None)`

Initialize writer with optional custom paths.

```python
from greeum.api.write import AnchorBasedWriter

writer = AnchorBasedWriter(
    db_manager=db_manager,
    anchor_path=Path("data/anchors.json"),
    graph_path=Path("data/graph_snapshot.jsonl")
)
```

#### `write(text, slot=None, keywords=None, tags=None, importance=None)`

Write a new block near specified anchor slot.

```python
# Write near anchor slot A
block_id = writer.write(
    text="New API endpoint implemented",
    slot='A',
    keywords=["api", "endpoint"],
    tags=["development"],
    importance=0.7
)
```

### AutoAnchorMovement

Intelligent anchor placement optimization based on usage patterns.

#### `evaluate_anchor_movement(slot, search_results, query_topic_vec)`

Evaluate whether an anchor should be moved.

```python
from greeum.anchors.auto_movement import AutoAnchorMovement

auto_movement = AutoAnchorMovement(anchor_manager, links_cache, db_manager)

evaluation = auto_movement.evaluate_anchor_movement(
    slot='A',
    search_results=recent_results,
    query_topic_vec=topic_embedding
)

if evaluation['should_move']:
    print(f"Recommended move: {evaluation['reason']}")
    print(f"Target block: {evaluation['target_block_id']}")
```

---

## CLI Commands

### Anchor Management Commands

#### `greeum anchors status`

Display current anchor status for all slots.

```bash
greeum anchors status
# Shows Rich-formatted table with anchor details

greeum anchors status --verbose
# Include additional metadata
```

#### `greeum anchors set <slot> <block_id>`

Set anchor for specified slot.

```bash
# Set anchor for slot A
greeum anchors set A 1234

# With custom summary and hop budget  
greeum anchors set B 5678 --summary "Machine learning project" --hop-budget 2
```

#### `greeum anchors pin/unpin <slot>`

Pin or unpin anchor to control automatic movement.

```bash
# Pin anchor (prevent auto-movement)
greeum anchors pin A

# Unpin anchor (allow auto-movement)
greeum anchors unpin A
```

### Search Commands

#### `greeum search <query>`

Enhanced search command with anchor support.

```bash
# Basic search (no anchors)
greeum search "machine learning algorithms"

# Anchor-based localized search
greeum search "neural networks" --slot A --radius 2

# Multiple search parameters
greeum search "data analysis" --slot B --radius 1 --fallback --limit 10
```

**Parameters:**
- `--slot` (A/B/C): Anchor slot for localized search
- `--radius` (int): Search radius in hops (default: 2)  
- `--fallback`: Enable global search fallback (default: true)
- `--limit` (int): Maximum results (default: 5)

---

## REST Endpoints

### Anchor Management

#### `GET /v1/anchors`

Get status of all anchor slots.

```bash
curl -X GET "http://localhost:5000/v1/anchors"
```

**Response:**
```json
{
  "version": 1,
  "slots": [
    {
      "slot": "A",
      "anchor_block_id": "1234",
      "hop_budget": 3,
      "pinned": false,
      "last_used_ts": 1693555200,
      "summary": "API development"
    }
  ],
  "updated_at": 1693555300
}
```

#### `PATCH /v1/anchors/{slot}`

Update anchor for specific slot.

```bash
curl -X PATCH "http://localhost:5000/v1/anchors/A" \
     -H "Content-Type: application/json" \
     -d '{
       "anchor_block_id": "9999",
       "summary": "New project context",
       "hop_budget": 2,
       "pinned": true
     }'
```

### Enhanced Search

#### `GET /api/v1/search`

Search with anchor support.

```bash
# Basic search
curl -X GET "http://localhost:5000/api/v1/search?query=machine+learning"

# Anchor-based search
curl -X GET "http://localhost:5000/api/v1/search?query=neural+networks&slot=A&radius=2&limit=5"
```

**Response:**
```json
{
  "results": [...],
  "metadata": {
    "local_search_used": true,
    "local_results": 3,
    "fallback_used": false,
    "search_time_ms": 12.5
  },
  "search_type": "anchor_based",
  "slot": "A",
  "radius": 2
}
```

---

## MCP Integration

### MCP Tools

Greeum provides 12 MCP tools for Claude Code integration:

#### Memory Management Tools

**add_memory**
```python
# Available in Claude Code
add_memory(
    content="Project milestone reached - API v2.0 deployed",
    keywords=["project", "milestone", "api"],
    importance=0.9
)
```

**search_memory**
```python
# Search with multiple methods
search_memory(
    query="project status",
    search_type="hybrid",  # keyword, embedding, hybrid
    limit=10
)
```

#### Analytics Tools

**usage_analytics**
```python
# Get usage insights
usage_analytics(
    days=30,
    detailed=True,
    include_trends=True
)
```

**get_memory_stats**
```python
# System statistics
get_memory_stats(
    include_quality=True,
    include_performance=True
)
```

#### Quality Tools

**quality_check**
```python
# Validate memory quality
quality_check(
    content="Memory content to validate",
    importance=0.7
)
```

**check_duplicates**
```python
# Check for duplicates
check_duplicates(
    content="Content to check",
    threshold=0.85
)
```

### MCP Server Configuration

#### Basic Configuration

```json
{
  "mcpServers": {
    "greeum": {
      "command": "python3",
      "args": ["-m", "greeum.mcp.claude_code_mcp_server"],
      "env": {
        "GREEUM_DATA_DIR": "/path/to/data",
        "GREEUM_LOG_LEVEL": "INFO"
      }
    }
  }
}
```

#### Advanced Configuration

```json
{
  "mcpServers": {
    "greeum": {
      "command": "python3",
      "args": ["-m", "greeum.mcp.claude_code_mcp_server"],
      "env": {
        "GREEUM_DATA_DIR": "/custom/data/path",
        "GREEUM_LOG_LEVEL": "DEBUG",
        "GREEUM_DB_TYPE": "postgresql",
        "GREEUM_CONNECTION_STRING": "postgresql://user:pass@localhost/greeum",
        "GREEUM_QUALITY_THRESHOLD": "0.7",
        "GREEUM_DUPLICATE_THRESHOLD": "0.85"
      }
    }
  }
}
```

---

## Embedding Models

### Built-in Models

#### SimpleEmbeddingModel

Basic hash-based embedding for development.

```python
from greeum.embedding_models import SimpleEmbeddingModel

model = SimpleEmbeddingModel(dimension=128)
embedding = model.encode("text to embed")
```

#### EmbeddingRegistry

Manage multiple embedding models.

```python
from greeum.embedding_models import EmbeddingRegistry

registry = EmbeddingRegistry()
registry.register_model("custom", custom_model, set_as_default=True)

# Use registered model
embedding = registry.get_embedding("text", model_name="custom")
```

### External Models (Optional)

#### Sentence Transformers

```python
# Requires: pip install sentence-transformers
from sentence_transformers import SentenceTransformer

model = SentenceTransformer('all-MiniLM-L6-v2')
embeddings = model.encode(["text1", "text2"])
```

#### OpenAI Embeddings

```python
# Requires: pip install openai
import openai

response = openai.embeddings.create(
    model="text-embedding-3-small",
    input="text to embed"
)
embedding = response.data[0].embedding
```

---

## Text Utils

Utility functions for text processing.

#### `extract_keywords(text, max_keywords=10)`

Extract keywords from text.

```python
from greeum.text_utils import extract_keywords

keywords = extract_keywords("Machine learning project with Python and TensorFlow")
# Returns: ["machine", "learning", "project", "python", "tensorflow"]
```

#### `process_user_input(text)`

Process user input with keyword extraction and embedding.

```python
from greeum.text_utils import process_user_input

result = process_user_input("Started working on the new API endpoints")
# Returns: {
#   "context": "Started working on the new API endpoints",
#   "keywords": ["started", "working", "api", "endpoints"],
#   "tags": ["work", "development"],
#   "embedding": [...],
#   "importance": 0.6
# }
```

#### `detect_language(text)`

Auto-detect text language.

```python
from greeum.text_utils import detect_language

lang = detect_language("안녕하세요 반갑습니다")  # Returns: "ko"
lang = detect_language("Hello, how are you?")   # Returns: "en"
```

---

## Error Handling

### Common Exceptions

```python
from greeum.exceptions import (
    GreeumError,
    DatabaseError, 
    EmbeddingError,
    ValidationError
)

try:
    bm.add_block(context, keywords, tags, embedding, importance)
except ValidationError as e:
    print(f"Invalid input: {e}")
except DatabaseError as e:
    print(f"Database error: {e}")
except GreeumError as e:
    print(f"General Greeum error: {e}")
```

### Best Practices

#### Memory Management

```python
# Always validate inputs
if not context or len(context.strip()) < 10:
    raise ValidationError("Context too short")

# Handle embedding failures gracefully
try:
    embedding = get_embedding(context)
except EmbeddingError:
    embedding = simple_embedding_fallback(context)

# Check for duplicates before adding
if not detector.check_duplicates(context)['is_duplicate']:
    bm.add_block(context, keywords, tags, embedding, importance)
```

#### Performance Optimization

```python
# Batch operations when possible
contexts = ["text1", "text2", "text3"]
embeddings = embedding_model.batch_encode(contexts)

for context, embedding in zip(contexts, embeddings):
    bm.add_block(context, keywords, tags, embedding, importance)

# Use appropriate limits
results = bm.search_by_embedding(query_emb, top_k=20)  # Not too high
recent = stm.get_recent_memories(count=10)  # Reasonable count
```

---

## Configuration

### Environment Variables

```bash
# Data directory
export GREEUM_DATA_DIR="/path/to/data"

# Database configuration  
export GREEUM_DB_TYPE="sqlite"  # or "postgres"
export GREEUM_CONNECTION_STRING="path/to/db.sqlite"

# Logging
export GREEUM_LOG_LEVEL="INFO"  # DEBUG, INFO, WARNING, ERROR

# Quality settings
export GREEUM_QUALITY_THRESHOLD="0.7"
export GREEUM_DUPLICATE_THRESHOLD="0.85"

# External API keys
export OPENAI_API_KEY="your-key-here"
```

### Configuration File

Create `~/.greeum/config.json`:

```json
{
  "database": {
    "type": "sqlite",
    "connection_string": "data/memory.db"
  },
  "embeddings": {
    "default_model": "simple",
    "cache_embeddings": true
  },
  "quality": {
    "auto_validate": true,
    "threshold": 0.7,
    "factors": {
      "length": {"weight": 0.1, "min_score": 0.3},
      "richness": {"weight": 0.2, "min_score": 0.4},
      "structure": {"weight": 0.15, "min_score": 0.3}
    }
  },
  "analytics": {
    "enabled": true,
    "retention_days": 90,
    "session_timeout": 1800
  },
  "cache": {
    "max_size": 100,
    "ttl": 3600
  }
}
```

---

## Version History

### v2.0.5 (Current)
- Enhanced MCP tool descriptions with usage guidelines
- Smart duplicate detection with 85% similarity threshold  
- Quality validation system with 7-factor assessment
- Usage analytics and monitoring system
- Improved CLI commands: `quality`, `analytics`, `optimize`

### v2.0.4
- Lightweight dependency optimization
- Enhanced MCP server stability
- Performance improvements

### v2.0.3
- MCP server integration improvements
- Bug fixes and stability enhancements

---

For more examples and tutorials, see:
- [Get Started Guide](get-started.md)
- [Tutorials](tutorials.md)
- [Official Website](https://greeum.app)

Contact: playtart@play-t.art
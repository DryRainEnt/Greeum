# Greeum Tutorials

Complete step-by-step guides for using Greeum v2.0.5 memory management system. Learn how to leverage intelligent memory, quality validation, and advanced MCP integration.

## Table of Contents

1. [Getting Started](#getting-started)
2. [Basic Memory Management](#basic-memory-management)
3. [Quality Management (v2.0.5)](#quality-management-v205)
4. [Advanced CLI Commands (v2.0.5)](#advanced-cli-commands-v205)
5. [MCP Integration with Claude Code](#mcp-integration-with-claude-code)
6. [Temporal Search](#temporal-search)
7. [Multi-language Support](#multi-language-support)
8. [Python API Usage](#python-api-usage)
9. [Advanced Features](#advanced-features)
10. [REST API Server](#rest-api-server)

## Getting Started

Learn how to install Greeum v2.0.5 and initialize the memory system.

### Installation

First, install Greeum following the [Get Started Guide](get-started.md):

```bash
# Install with pipx (recommended)
pipx install greeum

# Or install with pip
pip install greeum

# Verify installation
greeum --version  # Should show v2.0.5 or higher
```

### Quick Start

Get started with Greeum in 3 simple steps:

```bash
# Step 1: Add your first memory
python3 -m greeum.cli memory add "Started learning Greeum v2.0.5 - it has amazing quality validation features!"

# Step 2: Search memories
python3 -m greeum.cli memory search "learning Greeum" --limit 5

# Step 3: Analyze your memory patterns
python3 -m greeum.cli ltm analyze --period 7d
```

### Basic System Initialization

```python
from greeum import BlockManager, STMManager, PromptWrapper
from greeum.core.quality_validator import QualityValidator
from greeum.core.duplicate_detector import DuplicateDetector

# Initialize core memory components
block_manager = BlockManager()
stm_manager = STMManager(default_ttl=3600)  # 1 hour TTL
prompt_wrapper = PromptWrapper()

# Initialize v2.0.5 quality features
quality_validator = QualityValidator()
duplicate_detector = DuplicateDetector(similarity_threshold=0.85)

print("Greeum v2.0.5 initialized with quality validation!")
```

## Basic Memory Management

Learn the fundamentals of storing, retrieving, and managing memories with Greeum v2.0.5.

### Adding Memories with Quality Validation

```python
from greeum import BlockManager
from greeum.core.quality_validator import QualityValidator
from greeum.core.duplicate_detector import DuplicateDetector
from greeum.text_utils import process_user_input

# Initialize components
block_manager = BlockManager()
quality_validator = QualityValidator()
duplicate_detector = DuplicateDetector()

# Memory content
content = "Started a new machine learning project focused on developing an image recognition system using deep learning algorithms. The goal is to achieve 95% accuracy for medical diagnosis applications."

# Step 1: Validate quality before storing
quality_result = quality_validator.validate_memory_quality(content, importance=0.8)

print(f"Quality Score: {quality_result['quality_score']:.3f}")
print(f"Quality Level: {quality_result['quality_level']}")
print(f"Suggestions: {quality_result['suggestions']}")

# Step 2: Check for duplicates
duplicate_result = duplicate_detector.check_duplicates(content)

if duplicate_result['is_duplicate']:
    print(f"⚠️ Similar memory found with {duplicate_result['max_similarity']:.3f} similarity")
else:
    print("✅ No duplicates found")

# Step 3: Store memory if quality is acceptable
if quality_result['quality_score'] >= 0.6 and not duplicate_result['is_duplicate']:
    processed = process_user_input(content)
    
    block = block_manager.add_block(
        context=processed["context"],
        keywords=processed["keywords"],
        tags=processed["tags"],
        embedding=processed["embedding"],
        importance=0.8
    )
    
    print(f"✅ Memory stored successfully! Block index: {block['block_index']}")
else:
    print("❌ Memory not stored due to quality/duplicate issues")
```

### Searching Memories

```python
# Keyword search
keyword_results = block_manager.search_by_keywords(
    keywords=["machine learning", "project", "image"],
    limit=5
)

print(f"Keyword search results: {len(keyword_results)}")
for result in keyword_results:
    print(f"Block {result['block_index']}: {result['context'][:60]}...")

# Vector similarity search
from greeum.embedding_models import get_embedding

query = "Tell me about AI projects for medical applications"
query_embedding = get_embedding(query)

similarity_results = block_manager.search_by_embedding(
    query_embedding, 
    top_k=5
)

print(f"\nSimilarity search results: {len(similarity_results)}")
for result in similarity_results:
    print(f"Score: {result.get('similarity', 'N/A'):.3f} - {result['context'][:60]}...")
```

## Quality Management (v2.0.5)

Greeum v2.0.5 introduces intelligent quality management with 7-factor assessment.

### Understanding Quality Metrics

```python
from greeum.core.quality_validator import QualityValidator

validator = QualityValidator()

# Test different content quality levels
test_contents = [
    "Good",  # Too short
    "Attended team meeting about Q4 roadmap, resource allocation, and timeline adjustments. Discussed budget constraints and identified key milestones for product launch.",  # High quality
    "meeting stuff happened",  # Low quality
    "Today I successfully implemented the new authentication system using JWT tokens, integrated it with the existing user database, tested all edge cases, and documented the API endpoints for the development team."  # Very high quality
]

for i, content in enumerate(test_contents, 1):
    print(f"\n--- Test Content {i} ---")
    print(f"Content: {content}")
    
    result = validator.validate_memory_quality(content)
    
    print(f"Quality Score: {result['quality_score']:.3f}")
    print(f"Quality Level: {result['quality_level']}")
    print(f"Quality Factors:")
    
    for factor, score in result['quality_factors'].items():
        print(f"  {factor}: {score:.2f}")
    
    if result['suggestions']:
        print(f"Suggestions: {', '.join(result['suggestions'])}")
```

### Duplicate Detection

```python
from greeum.core.duplicate_detector import DuplicateDetector

detector = DuplicateDetector(similarity_threshold=0.85)

# Add initial memory
initial_content = "Working on machine learning project for image classification"
block_manager.add_block(
    context=initial_content,
    keywords=["machine", "learning", "image", "classification"]
)

# Test for duplicates
similar_contents = [
    "Working on ML project for image classification",  # Very similar
    "Developing image classification using machine learning",  # Similar concept
    "Started a cooking tutorial project",  # Different topic
]

for content in similar_contents:
    result = detector.check_duplicates(content)
    
    print(f"\nContent: {content}")
    print(f"Is duplicate: {result['is_duplicate']}")
    print(f"Max similarity: {result['max_similarity']:.3f}")
    
    if result['similar_memories']:
        print(f"Found {len(result['similar_memories'])} similar memories")
```

### Short-term Memory Management

```python
from greeum import STMManager

# Initialize STM with custom TTL
stm_manager = STMManager(default_ttl=3600)  # 1 hour

# Add short-term memories with different TTLs
memories = [
    {"content": "Meeting scheduled for 3 PM today", "ttl": 3600},      # 1 hour
    {"content": "Project deadline is next Friday", "ttl": 86400},     # 1 day  
    {"content": "New ML algorithm achieved 98.5% accuracy", "ttl": 604800}  # 1 week
]

for memory in memories:
    memory_data = {
        "id": f"stm_{hash(memory['content']) % 10000}",
        "content": memory["content"],
        "importance": 0.7
    }
    
    stm_manager.add_memory(memory_data, ttl=memory["ttl"])
    print(f"Added STM: {memory['content']} (TTL: {memory['ttl']}s)")

# Retrieve recent memories
recent = stm_manager.get_recent_memories(count=5)
print(f"\nRecent STM entries: {len(recent)}")

for mem in recent:
    print(f"- {mem['content']} (importance: {mem.get('importance', 'N/A')})")
```

## Advanced CLI Commands (v2.0.5)

Explore the new CLI commands introduced in Greeum v2.0.5.

### Python API: Quality Validation

```python
from greeum.core.quality_validator import QualityValidator

validator = QualityValidator()
result = validator.validate_memory_quality(
    "Comprehensive project analysis completed with detailed findings and recommendations"
)

print(f"Quality Score: {result['quality_score']:.3f}")
print(f"Quality Level: {result['quality_level']}")
# Output:
# Quality Score: 0.847
# Quality Level: good
```

### Python API: Usage Analytics

```python
from greeum.core.usage_analytics import UsageAnalytics

analytics = UsageAnalytics()
stats = analytics.get_usage_statistics(days=30)

print(f"Total Events: {stats['total_events']}")
print(f"Success Rate: {stats['success_rate']:.1%}")
# Access via Python API for detailed analytics
```

### Memory Management via CLI

```bash
# Analyze long-term memory patterns
python3 -m greeum.cli ltm analyze --period 30d --trends

# Manage short-term memory
python3 -m greeum.cli stm cleanup --expired
python3 -m greeum.cli stm promote --threshold 0.8

# Export memory data
python3 -m greeum.cli ltm export --format json --limit 1000
```

### Advanced Search via CLI

```bash
# Basic memory search
python3 -m greeum.cli memory search "machine learning project" --limit 10

# Search in long-term memory with analysis
python3 -m greeum.cli ltm analyze --period 1d

# Add specific search terms to short-term memory
python3 -m greeum.cli stm add "Searching for ML project info" --ttl 30m
```

## MCP Integration with Claude Code

Learn how to integrate Greeum with Claude Code using MCP (Model Control Protocol).

### Setting Up MCP Integration

1. **Install Greeum MCP Server**:
   ```bash
   # Install GreeumMCP package
   pip install greeummcp
   
   # Verify installation
   python -m greeum.mcp.claude_code_mcp_server --help
   ```

2. **Configure Claude Desktop**:
   
   Edit your Claude Desktop configuration (`~/.config/claude-desktop/claude_desktop_config.json`):
   
   ```json
   {
     "mcpServers": {
       "greeum": {
         "command": "python3",
         "args": ["-m", "greeum.mcp.claude_code_mcp_server"],
         "env": {
           "GREEUM_DATA_DIR": "/path/to/your/data",
           "GREEUM_LOG_LEVEL": "INFO"
         }
       }
     }
   }
   ```

3. **Verify Connection**:
   ```bash
   claude mcp list
   # Should show: greeum - ✓ Connected
   ```

### Using MCP Tools in Claude Code

Once configured, you can use these 12 MCP tools in Claude Code:

#### Memory Management Tools
```python
# In Claude Code, these tools are available directly:

# Add new memory
add_memory(
    content="Completed implementation of user authentication system",
    keywords=["authentication", "implementation", "completed"],
    importance=0.9
)

# Search memories  
search_memory(
    query="authentication system",
    search_type="hybrid",  # keyword, embedding, or hybrid
    limit=10
)

# Get system statistics
get_memory_stats(
    include_quality=True,
    include_performance=True
)
```

#### Quality and Analytics Tools
```python
# Validate memory quality
quality_check(
    content="Memory content to validate for quality assessment",
    importance=0.7
)

# Check for duplicates
check_duplicates(
    content="Content to check for similar existing memories",
    threshold=0.85
)

# Get usage analytics
usage_analytics(
    days=30,
    detailed=True,
    include_trends=True
)
```

#### Long-term Memory Tools
```python
# Analyze LTM patterns
ltm_analyze(
    period="30d",
    trends=True,
    output="text"  # or "json"
)

# Verify LTM integrity
ltm_verify(
    repair=False  # Set to True to attempt repairs
)

# Export LTM data
ltm_export(
    format="json",  # "json", "csv", or "blockchain"
    limit=1000
)
```

#### Short-term Memory Tools
```python
# Add STM entry
stm_add(
    content="Temporary information for current session",
    ttl="2h",
    importance=0.6
)

# Promote STM to LTM
stm_promote(
    threshold=0.8,
    dry_run=False
)

# Clean up STM
stm_cleanup(
    expired=True,
    smart=True,
    threshold=0.3
)
```
```

## Temporal Search

Utilize Greeum's advanced temporal reasoning for time-based memory retrieval.

### Natural Language Time Expressions

```python
from greeum import TemporalReasoner

# Initialize temporal reasoner
temporal_reasoner = TemporalReasoner()

# Test various time expressions
time_queries = [
    "What did I work on yesterday?",
    "Show me tasks from last week",
    "Find memories from 3 days ago",
    "어제 회의에서 뭘 결정했지?",  # Korean
    "昨日の作業内容を教えて",        # Japanese
    "上周的项目进展如何？"         # Chinese
]

for query in time_queries:
    print(f"\nQuery: {query}")
    
    # Search with temporal reasoning
    results = temporal_reasoner.search_by_time(query, top_k=5)
    
    print(f"Language detected: {results.get('language', 'auto')}")
    print(f"Time expression found: {results.get('time_reference', 'none')}")
    print(f"Results: {len(results.get('blocks', []))} memories found")
    
    # Display results
    for block in results.get('blocks', [])[:2]:  # Show first 2
        timestamp = block.get('timestamp', 'Unknown')
        content = block.get('context', '')[:50] + '...'
        print(f"  [{timestamp}] {content}")
```

### Time Range Search

```python
from datetime import datetime, timedelta

# Search within specific time range
end_date = datetime.now()
start_date = end_date - timedelta(days=7)  # Last 7 days

range_results = block_manager.get_blocks_by_time_range(
    start_date=start_date,
    end_date=end_date,
    limit=20
)

print(f"Memories from last 7 days: {len(range_results)}")

# Group by day
from collections import defaultdict

memories_by_day = defaultdict(list)
for block in range_results:
    day = block['timestamp'][:10]  # YYYY-MM-DD
    memories_by_day[day].append(block)

for day, day_memories in sorted(memories_by_day.items()):
    print(f"\n{day}: {len(day_memories)} memories")
    for memory in day_memories[:2]:  # Show first 2 per day
        print(f"  - {memory['context'][:40]}...")
```

## Multi-language Support

Leverage Greeum's comprehensive multi-language capabilities for Korean, English, Japanese, and Chinese.

### Automatic Language Detection

```python
from greeum.text_utils import detect_language, extract_keywords
from greeum import BlockManager

block_manager = BlockManager()

# Multi-language content examples
multilingual_content = [
    {"text": "오늘 머신러닝 프로젝트 회의를 했습니다.", "expected": "ko"},
    {"text": "We had a machine learning project meeting today.", "expected": "en"},
    {"text": "今日は機械学習プロジェクトの会議をしました。", "expected": "ja"},
    {"text": "今天我们开了机器学习项目会议。", "expected": "zh"},
    {"text": "프로젝트 meeting was very productive today.", "expected": "mixed"}
]

for item in multilingual_content:
    text = item["text"]
    
    # Detect language
    detected_lang = detect_language(text)
    
    # Extract keywords with auto-detection
    keywords = extract_keywords(text, language="auto")
    
    print(f"\nText: {text}")
    print(f"Expected: {item['expected']}, Detected: {detected_lang}")
    print(f"Keywords: {keywords}")
    
    # Store memory with detected language metadata
    block_manager.add_block(
        context=text,
        keywords=keywords,
        tags=["multilingual", "meeting"],
        importance=0.7,
        metadata={"language": detected_lang}
    )
```

### Cross-language Search

```python
# Search across different languages
search_queries = [
    "machine learning meeting",  # English
    "머신러닝 회의",              # Korean
    "機械学習 会議",              # Japanese
    "机器学习 会议"               # Chinese
]

for query in search_queries:
    print(f"\nSearching for: {query}")
    
    # Perform semantic search (works across languages)
    from greeum.embedding_models import get_embedding
    
    query_embedding = get_embedding(query)
    results = block_manager.search_by_embedding(query_embedding, top_k=3)
    
    print(f"Found {len(results)} results:")
    for result in results:
        lang = result.get('metadata', {}).get('language', 'unknown')
        print(f"  [{lang}] {result['context'][:50]}...")
```

### Multi-language Temporal Expressions

```python
# Multi-language temporal expression examples
time_expressions = {
    "Korean": [
        "어제 회의에서 결정한 사항",
        "3일 전에 작성한 문서", 
        "지난주 프로젝트 진행상황",
        "이번 달 목표 설정"
    ],
    "English": [
        "yesterday's meeting decisions",
        "document written 3 days ago",
        "last week's project progress", 
        "this month's goal setting"
    ],
    "Japanese": [
        "昨日の会議での決定事項",
        "3日前に作成した文書",
        "先週のプロジェクト進捗",
        "今月の目標設定"
    ],
    "Chinese": [
        "昨天会议的决定",
        "3天前写的文档", 
        "上周的项目进展",
        "本月的目标设定"
    ]
}

for language, expressions in time_expressions.items():
    print(f"\n{language} temporal expressions:")
    for expr in expressions:
        # Search using temporal reasoning
        results = temporal_reasoner.search_by_time(expr, top_k=3)
        
        print(f"  Query: '{expr}'")
        print(f"  Time reference detected: {results.get('time_reference', 'none')}")
        print(f"  Results found: {len(results.get('blocks', []))}")
    print("-" * 60)
```

## Python API Usage

Comprehensive Python API examples for integrating Greeum into your applications.

### Enhanced Prompt Generation

```python
from greeum import BlockManager, STMManager, CacheManager, PromptWrapper
from greeum.core.quality_validator import QualityValidator
from greeum.embedding_models import get_embedding

# Initialize system with quality validation
block_manager = BlockManager()
stm_manager = STMManager()
cache_manager = CacheManager(block_manager=block_manager)
quality_validator = QualityValidator()
prompt_wrapper = PromptWrapper(cache_manager=cache_manager, stm_manager=stm_manager)

# Add some high-quality memories
memories = [
    {
        "context": "Successfully implemented authentication system using JWT tokens with refresh mechanism. Integrated with existing user database, added rate limiting, and comprehensive error handling.",
        "keywords": ["authentication", "JWT", "security", "implementation"],
        "importance": 0.9
    },
    {
        "context": "Client requested prototype delivery by next Friday. Scope includes user login, dashboard, and basic CRUD operations. Team allocated: 2 developers, 1 designer.",
        "keywords": ["client", "prototype", "deadline", "scope"],
        "importance": 0.8
    }
]

for memory in memories:
    # Validate quality before storing
    quality_result = quality_validator.validate_memory_quality(
        memory["context"], 
        importance=memory["importance"]
    )
    
    if quality_result["quality_score"] >= 0.7:
        block_manager.add_block(
            context=memory["context"],
            keywords=memory["keywords"],
            tags=["work", "development"],
            embedding=get_embedding(memory["context"]),
            importance=memory["importance"]
        )
        print(f"✅ Added memory (quality: {quality_result['quality_score']:.3f})")

# Add short-term context
stm_memory = {
    "id": "current_session",
    "content": "User is asking about project status. Show recent developments and upcoming deadlines.",
    "importance": 0.7
}
stm_manager.add_memory(stm_memory)

# Generate enhanced prompt
user_question = "What's the current status of our development project?"

# Update cache with current context
question_embedding = get_embedding(user_question)
cache_manager.update_cache(
    query_text=user_question,
    query_embedding=question_embedding,
    query_keywords=["project", "status", "development"]
)

# Compose prompt with memory context
enhanced_prompt = prompt_wrapper.compose_prompt(
    user_input=user_question,
    include_stm=True,
    max_context_length=2000
)

print("\n=== Enhanced Prompt with Memory Context ===")
print(enhanced_prompt)
print("\n" + "=" * 50)

# Simulate LLM response processing
llm_response = "Based on the current project status, we have successfully implemented the authentication system and are on track for the prototype delivery by next Friday."

# Store the interaction as a new memory
interaction_context = f"User asked: {user_question}\nResponse: {llm_response}"
interaction_quality = quality_validator.validate_memory_quality(interaction_context)

if interaction_quality["quality_score"] >= 0.6:
    block_manager.add_block(
        context=interaction_context,
        keywords=["interaction", "status", "update"],
        tags=["conversation", "project"],
        embedding=get_embedding(interaction_context),
        importance=0.7
    )
    print(f"💾 Stored interaction (quality: {interaction_quality['quality_score']:.3f})")
```

### Building Intelligent Agents

```python
class IntelligentAgent:
    """An AI agent with persistent memory using Greeum"""
    
    def __init__(self, agent_name: str):
        self.name = agent_name
        self.block_manager = BlockManager()
        self.stm_manager = STMManager()
        self.cache_manager = CacheManager(self.block_manager)
        self.prompt_wrapper = PromptWrapper(self.cache_manager, self.stm_manager)
        self.quality_validator = QualityValidator()
    
    def learn(self, information: str, importance: float = 0.7, tags: list = None):
        """Learn new information with quality validation"""
        quality_result = self.quality_validator.validate_memory_quality(
            information, importance=importance
        )
        
        if quality_result["quality_score"] >= 0.5:
            from greeum.text_utils import process_user_input
            processed = process_user_input(information)
            
            self.block_manager.add_block(
                context=processed["context"],
                keywords=processed["keywords"],
                tags=tags or processed["tags"],
                embedding=processed["embedding"],
                importance=importance
            )
            
            return f"✅ Learned: {information[:50]}... (Quality: {quality_result['quality_score']:.3f})"
        else:
            return f"❌ Information quality too low ({quality_result['quality_score']:.3f})"
    
    def remember(self, query: str, max_memories: int = 5):
        """Remember relevant information based on query"""
        query_embedding = get_embedding(query)
        
        # Update cache with current query context
        from greeum.text_utils import extract_keywords
        keywords = extract_keywords(query)
        
        self.cache_manager.update_cache(
            query_text=query,
            query_embedding=query_embedding,
            query_keywords=keywords
        )
        
        # Get relevant memories
        relevant_memories = self.cache_manager.get_relevant_memories(limit=max_memories)
        
        return relevant_memories
    
    def think(self, user_input: str):
        """Generate contextual response using memory"""
        # Remember relevant information
        memories = self.remember(user_input)
        
        # Add current input to short-term memory
        stm_entry = {
            "id": f"input_{hash(user_input) % 10000}",
            "content": user_input,
            "importance": 0.6
        }
        self.stm_manager.add_memory(stm_entry)
        
        # Generate enhanced prompt
        prompt = self.prompt_wrapper.compose_prompt(
            user_input=user_input,
            include_stm=True,
            max_context_length=1500
        )
        
        return {
            "prompt": prompt,
            "relevant_memories": len(memories),
            "memory_context": [mem["context"][:100] + "..." for mem in memories[:3]]
        }

# Example usage
agent = IntelligentAgent("DevAssistant")

# Teach the agent
learning_results = [
    agent.learn("Python FastAPI framework is excellent for building REST APIs with automatic OpenAPI documentation.", importance=0.8, tags=["python", "api", "documentation"]),
    agent.learn("JWT tokens should be stored securely and have reasonable expiration times for security.", importance=0.9, tags=["security", "jwt", "best-practices"]),
    agent.learn("Code reviews improve code quality and help knowledge sharing among team members.", importance=0.7, tags=["development", "quality", "teamwork"])
]

for result in learning_results:
    print(result)

# Ask the agent something
user_question = "How should I implement secure API authentication?"
thought_process = agent.think(user_question)

print(f"\n🤔 Thinking about: {user_question}")
print(f"📚 Relevant memories found: {thought_process['relevant_memories']}")
print(f"🧠 Memory context preview:")
for i, context in enumerate(thought_process['memory_context'], 1):
    print(f"  {i}. {context}")

print(f"\n📝 Generated prompt:")
print(thought_process['prompt'])
```

### Custom Prompt Templates

```python
# Define custom prompt templates for different use cases

# Technical Assistant Template
tech_template = """
You are an expert technical assistant with persistent memory.

RELEVANT TECHNICAL KNOWLEDGE:
{memory_blocks}

RECENT CONTEXT:
{short_term_memories}

USER QUERY: {user_input}

Provide a detailed technical response based on your knowledge and context. Include:
1. Direct answer to the question
2. Relevant technical details
3. Best practices or recommendations
4. Related concepts from your memory
"""

# Creative Assistant Template  
creative_template = """
You are a creative assistant with rich experiential memory.

INSPIRATIONAL MEMORIES:
{memory_blocks}

CURRENT SESSION CONTEXT:
{short_term_memories}

CREATIVE REQUEST: {user_input}

Draw upon your memories to provide a creative, innovative response. Consider:
- Past successful approaches
- Creative patterns and techniques
- Unexpected connections between ideas
- Lessons learned from previous projects
"""

# Project Manager Template
project_template = """
You are an experienced project manager with comprehensive project memory.

PROJECT HISTORY & DECISIONS:
{memory_blocks}

CURRENT PROJECT STATUS:
{short_term_memories}

PROJECT QUERY: {user_input}

Provide strategic project guidance considering:
- Historical project data and outcomes
- Previous decisions and their results
- Team capabilities and constraints
- Risk factors and mitigation strategies
- Timeline and resource implications
"""

# Example: Using different templates
templates = {
    "technical": tech_template,
    "creative": creative_template,
    "project": project_template
}

def get_contextual_response(query: str, template_type: str = "technical"):
    """Generate response using specific template type"""
    
    # Set the appropriate template
    template = templates.get(template_type, tech_template) 
    prompt_wrapper.set_template(template)
    
    # Generate prompt with memory context
    enhanced_prompt = prompt_wrapper.compose_prompt(
        user_input=query,
        include_stm=True,
        max_context_length=2000
    )
    
    return enhanced_prompt

# Test different templates
test_queries = [
    {"query": "How can I optimize database queries?", "type": "technical"},
    {"query": "I need creative ideas for user engagement", "type": "creative"},
    {"query": "What's our project timeline looking like?", "type": "project"}
]

for test in test_queries:
    print(f"\n=== {test['type'].upper()} TEMPLATE ===")
    print(f"Query: {test['query']}")
    prompt = get_contextual_response(test["query"], test["type"])
    print(f"Generated prompt: {len(prompt)} characters")
    print(f"Preview: {prompt[:200]}...")
```
```

## Advanced Features

Explore Greeum v2.0.5's advanced capabilities for production use.

### Hybrid Search Engine

```python
from greeum.core.search_engine import SearchEngine, BertReranker

# Initialize advanced search with BERT reranking
try:
    # Optional: Use BERT cross-encoder for better relevance
    reranker = BertReranker("cross-encoder/ms-marco-MiniLM-L-6-v2")
    search_engine = SearchEngine(block_manager=block_manager, reranker=reranker)
    print("🚀 Advanced search engine with BERT reranking enabled")
except ImportError:
    # Fallback to standard search
    search_engine = SearchEngine(block_manager=block_manager)
    print("📊 Standard search engine enabled")

# Perform advanced search
complex_queries = [
    "machine learning algorithms for natural language processing",
    "database optimization techniques for large datasets",
    "user authentication security best practices"
]

for query in complex_queries:
    print(f"\n🔍 Searching: {query}")
    
    # Advanced search with timing
    results = search_engine.search(query, top_k=5)
    
    print(f"📈 Performance metrics:")
    print(f"  - Total time: {results['timing']['total_time']:.0f}ms")
    print(f"  - Vector search: {results['timing']['vector_search']:.0f}ms")
    print(f"  - Reranking: {results['timing'].get('reranking', 0):.0f}ms")
    
    print(f"📚 Results ({len(results['blocks'])}):") 
    for i, block in enumerate(results["blocks"][:3], 1):
        relevance = block.get("relevance_score", "N/A")
        print(f"  {i}. [Score: {relevance}] {block['context'][:80]}...")
```

### Memory Analytics and Monitoring

```python
from greeum.core.usage_analytics import UsageAnalytics
import time

# Initialize analytics system
analytics = UsageAnalytics()

# Simulate various operations with logging
operations = [
    {"type": "tool_usage", "tool": "add_memory", "duration": 120, "success": True},
    {"type": "tool_usage", "tool": "search_memory", "duration": 85, "success": True},
    {"type": "tool_usage", "tool": "quality_check", "duration": 45, "success": True},
    {"type": "tool_usage", "tool": "search_memory", "duration": 95, "success": False},
    {"type": "system_event", "tool": "optimization", "duration": 300, "success": True},
]

for op in operations:
    analytics.log_event(
        event_type=op["type"],
        tool_name=op["tool"],
        duration_ms=op["duration"],
        success=op["success"],
        metadata={"simulated": True}
    )
    time.sleep(0.1)  # Small delay between operations

# Get comprehensive usage statistics
stats = analytics.get_usage_statistics(days=7)

print("📊 Usage Analytics Report:")
print(f"  Total Events: {stats['total_events']}")
print(f"  Unique Sessions: {stats['unique_sessions']}")
print(f"  Success Rate: {stats['success_rate']*100:.1f}%")
print(f"  Avg Response Time: {stats['avg_response_time']:.0f}ms")

if 'tool_usage' in stats:
    print(f"\n🔧 Most Used Tools:")
    for tool, count in stats['tool_usage'].items():
        print(f"    {tool}: {count} uses")

# Get quality trends
quality_trends = analytics.get_quality_trends(days=7)
if quality_trends:
    print(f"\n📈 Quality Trends:")
    print(f"  Average Quality: {quality_trends['avg_quality_score']:.3f}")
    print(f"  High Quality Ratio: {quality_trends['high_quality_ratio']*100:.1f}%")
```

### Memory System Optimization

```python
from greeum.core.duplicate_detector import DuplicateDetector
from greeum.core.quality_validator import QualityValidator

class MemoryOptimizer:
    """Advanced memory system optimization"""
    
    def __init__(self, block_manager, stm_manager):
        self.block_manager = block_manager
        self.stm_manager = stm_manager
        self.duplicate_detector = DuplicateDetector(similarity_threshold=0.85)
        self.quality_validator = QualityValidator()
    
    def optimize_long_term_memory(self, min_quality=0.5):
        """Optimize LTM by removing low-quality and duplicate memories"""
        all_blocks = self.block_manager.get_blocks(limit=1000)
        
        removed_count = 0
        duplicate_count = 0
        low_quality_count = 0
        
        print(f"🔧 Optimizing {len(all_blocks)} memories...")
        
        for block in all_blocks:
            block_id = block['block_index']
            content = block['context']
            
            # Check quality
            quality_result = self.quality_validator.validate_memory_quality(content)
            quality_score = quality_result['quality_score']
            
            # Check for duplicates
            duplicate_result = self.duplicate_detector.check_duplicates(content)
            
            should_remove = False
            reason = ""
            
            if quality_score < min_quality:
                should_remove = True
                reason = f"low quality ({quality_score:.3f})"
                low_quality_count += 1
            elif duplicate_result['is_duplicate'] and duplicate_result['max_similarity'] > 0.90:
                should_remove = True
                reason = f"duplicate ({duplicate_result['max_similarity']:.3f} similarity)"
                duplicate_count += 1
            
            if should_remove:
                # In a real implementation, you'd have a method to remove blocks
                print(f"  ❌ Would remove block {block_id}: {reason}")
                removed_count += 1
        
        print(f"\n✅ Optimization complete:")
        print(f"  - Low quality removed: {low_quality_count}")
        print(f"  - Duplicates removed: {duplicate_count}")
        print(f"  - Total removed: {removed_count}")
        print(f"  - Remaining: {len(all_blocks) - removed_count}")
        
        return {
            "total_processed": len(all_blocks),
            "removed": removed_count,
            "low_quality": low_quality_count,
            "duplicates": duplicate_count
        }
    
    def optimize_short_term_memory(self, importance_threshold=0.8):
        """Promote important STM entries to LTM"""
        stm_memories = self.stm_manager.get_recent_memories(count=100)
        
        promoted_count = 0
        
        for memory in stm_memories:
            importance = memory.get('importance', 0.5)
            
            if importance >= importance_threshold:
                # Convert STM to LTM format
                from greeum.text_utils import process_user_input
                processed = process_user_input(memory['content'])
                
                self.block_manager.add_block(
                    context=processed["context"],
                    keywords=processed["keywords"],
                    tags=processed["tags"] + ["promoted_from_stm"],
                    embedding=processed["embedding"],
                    importance=importance
                )
                
                promoted_count += 1
                print(f"⬆️ Promoted to LTM: {memory['content'][:50]}... (importance: {importance:.2f})")
        
        print(f"\n📈 STM Optimization: {promoted_count} memories promoted to LTM")
        return promoted_count

# Example usage
optimizer = MemoryOptimizer(block_manager, stm_manager)

print("=== Memory System Optimization ===")
ltm_results = optimizer.optimize_long_term_memory(min_quality=0.6)
stm_results = optimizer.optimize_short_term_memory(importance_threshold=0.7)

print(f"\n📊 Optimization Summary:")
print(f"  LTM processed: {ltm_results['total_processed']} memories")
print(f"  LTM optimized: {ltm_results['removed']} removed")
print(f"  STM promoted: {stm_results} memories")
```
```

### Production Configuration

```python
# Production-ready configuration example
import os
from greeum import BlockManager, STMManager
from greeum.core import DatabaseManager

# Environment-based configuration
class ProductionGreeumConfig:
    def __init__(self):
        self.data_dir = os.getenv('GREEUM_DATA_DIR', '/opt/greeum/data')
        self.db_type = os.getenv('GREEUM_DB_TYPE', 'sqlite')
        self.log_level = os.getenv('GREEUM_LOG_LEVEL', 'INFO')
        self.quality_threshold = float(os.getenv('GREEUM_QUALITY_THRESHOLD', '0.7'))
        self.duplicate_threshold = float(os.getenv('GREEUM_DUPLICATE_THRESHOLD', '0.85'))
        
        # Database configuration
        if self.db_type == 'postgresql':
            self.connection_string = os.getenv('GREEUM_CONNECTION_STRING')
        else:
            self.connection_string = os.path.join(self.data_dir, 'memory.db')
    
    def initialize_system(self):
        """Initialize production Greeum system"""
        # Ensure data directory exists
        os.makedirs(self.data_dir, exist_ok=True)
        
        # Initialize database manager
        db_manager = DatabaseManager(
            connection_string=self.connection_string,
            db_type=self.db_type
        )
        
        # Initialize components with production settings
        block_manager = BlockManager(db_manager=db_manager)
        stm_manager = STMManager(
            db_manager=db_manager,
            default_ttl=3600  # 1 hour default
        )
        
        print(f"✅ Greeum production system initialized")
        print(f"   Data directory: {self.data_dir}")
        print(f"   Database type: {self.db_type}")
        print(f"   Quality threshold: {self.quality_threshold}")
        
        return block_manager, stm_manager

# Usage
config = ProductionGreeumConfig()
block_manager, stm_manager = config.initialize_system()
```
```

## REST API Server

Greeum v2.0.5 provides a comprehensive REST API for integration with web applications and services.

### Starting the API Server

```bash
# Start the REST API server
python -m greeum.api.memory_api

# Server runs on http://localhost:5000
# Swagger documentation available at http://localhost:5000/api/v1/docs
```

### API Endpoints Overview

#### Health and Status
```bash
# Health check
curl http://localhost:5000/api/v1/health

# System statistics
curl http://localhost:5000/api/v1/stats
```

#### Memory Management
```bash
# Add memory with quality validation
curl -X POST http://localhost:5000/api/v1/memories \
  -H "Content-Type: application/json" \
  -d '{
    "content": "Implemented new caching system that improved API response time by 40%",
    "keywords": ["caching", "performance", "api"],
    "importance": 0.8,
    "validate_quality": true
  }'

# Search memories (hybrid approach)
curl "http://localhost:5000/api/v1/memories/search?q=caching%20performance&method=hybrid&limit=5"

# Get memory by ID
curl http://localhost:5000/api/v1/memories/123
```

#### Quality and Analytics
```bash
# Validate content quality
curl -X POST http://localhost:5000/api/v1/quality/validate \
  -H "Content-Type: application/json" \
  -d '{"content": "Content to validate", "importance": 0.7}'

# Check for duplicates
curl -X POST http://localhost:5000/api/v1/quality/duplicates \
  -H "Content-Type: application/json" \
  -d '{"content": "Content to check for duplicates"}'

# Get usage analytics
curl "http://localhost:5000/api/v1/analytics?days=30&detailed=true"
```
```

### Python Client Library

```python
import requests
import json
from typing import List, Dict, Optional

class GreeumAPIClient:
    """Professional Python client for Greeum v2.0.5 API"""
    
    def __init__(self, base_url: str = "http://localhost:5000/api/v1", api_key: Optional[str] = None):
        self.base_url = base_url
        self.session = requests.Session()
        
        if api_key:
            self.session.headers.update({"Authorization": f"Bearer {api_key}"})
    
    def add_memory(self, content: str, keywords: List[str] = None, 
                   importance: float = 0.7, validate_quality: bool = True) -> Dict:
        """Add new memory with optional quality validation"""
        data = {
            "content": content,
            "keywords": keywords or [],
            "importance": importance,
            "validate_quality": validate_quality
        }
        
        response = self.session.post(f"{self.base_url}/memories", json=data)
        response.raise_for_status()
        return response.json()
    
    def search_memories(self, query: str, method: str = "hybrid", 
                       limit: int = 10, min_quality: float = None) -> Dict:
        """Search memories using various methods"""
        params = {
            "q": query,
            "method": method,  # keyword, embedding, hybrid
            "limit": limit
        }
        
        if min_quality:
            params["min_quality"] = min_quality
        
        response = self.session.get(f"{self.base_url}/memories/search", params=params)
        response.raise_for_status()
        return response.json()
    
    def validate_quality(self, content: str, importance: float = 0.7) -> Dict:
        """Validate content quality"""
        data = {"content": content, "importance": importance}
        response = self.session.post(f"{self.base_url}/quality/validate", json=data)
        response.raise_for_status()
        return response.json()
    
    def check_duplicates(self, content: str, threshold: float = 0.85) -> Dict:
        """Check for duplicate content"""
        data = {"content": content, "threshold": threshold}
        response = self.session.post(f"{self.base_url}/quality/duplicates", json=data)
        response.raise_for_status()
        return response.json()
    
    def get_analytics(self, days: int = 7, detailed: bool = False) -> Dict:
        """Get usage analytics"""
        params = {"days": days, "detailed": detailed}
        response = self.session.get(f"{self.base_url}/analytics", params=params)
        response.raise_for_status()
        return response.json()
    
    def get_system_stats(self) -> Dict:
        """Get system statistics"""
        response = self.session.get(f"{self.base_url}/stats")
        response.raise_for_status()
        return response.json()

# Example usage
client = GreeumAPIClient()

# Add high-quality memory
print("Adding memory...")
memory_result = client.add_memory(
    content="Successfully implemented distributed caching system using Redis cluster. Achieved 40% performance improvement in API response times and 60% reduction in database load.",
    keywords=["redis", "caching", "performance", "distributed"],
    importance=0.9,
    validate_quality=True
)

print(f"✅ Memory added: {memory_result['success']}")
if 'quality_score' in memory_result:
    print(f"📊 Quality score: {memory_result['quality_score']:.3f}")

# Search with different methods
print("\n🔍 Searching memories...")
search_methods = ["keyword", "embedding", "hybrid"]

for method in search_methods:
    results = client.search_memories(
        query="caching performance optimization",
        method=method,
        limit=3
    )
    
    print(f"\n{method.upper()} search: {len(results.get('memories', []))} results")
    for i, memory in enumerate(results.get('memories', [])[:2], 1):
        score = memory.get('relevance_score', 'N/A')
        print(f"  {i}. [Score: {score}] {memory['content'][:60]}...")

# Get analytics
print("\n📈 System Analytics:")
analytics = client.get_analytics(days=30, detailed=True)
print(f"Total memories: {analytics.get('total_memories', 'N/A')}")
print(f"Average quality: {analytics.get('avg_quality_score', 'N/A')}")
print(f"Search performance: {analytics.get('avg_search_time', 'N/A')}ms")

# Validate content quality
print("\n🔍 Quality validation:")
test_content = "This is a very short text."
quality_result = client.validate_quality(test_content)
print(f"Quality score: {quality_result['quality_score']:.3f}")
print(f"Suggestions: {', '.join(quality_result.get('suggestions', []))}")
```

---

## Conclusion

This comprehensive tutorial covered Greeum v2.0.5's advanced features:

✅ **Quality Management**: 7-factor assessment system
✅ **Advanced CLI**: New `quality`, `analytics`, `optimize` commands
✅ **MCP Integration**: 12 tools for Claude Code
✅ **Multi-language Support**: Korean, English, Japanese, Chinese
✅ **Production Features**: Analytics, optimization, monitoring
✅ **REST API**: Complete web service integration

For more information:
- [Get Started Guide](get-started.md) - Installation and setup
- [API Reference](api-reference.md) - Complete API documentation  
- [Official Website](https://greeum.app) - Latest updates and resources

Contact: playtart@play-t.art
```

 

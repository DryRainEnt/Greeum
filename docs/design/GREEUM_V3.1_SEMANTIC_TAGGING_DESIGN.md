# Greeum v3.1: Systematic Semantic Tagging Design
## 체계적인 의미 기반 태깅 시스템 설계

---

## 🎯 **핵심 목표**

1. **검색 정확도 30% 향상** - 의미 기반 검색 가능
2. **언어 장벽 해결** - 한글 메모리를 영어 태그로 검색
3. **자동화 + 사용자 제어** - AI 자동 태깅 + 수동 오버라이드
4. **유지보수 최소화** - 태그 자동 정리 및 통합

---

## 📐 **시스템 아키텍처**

### 1. **3-Layer Tag Hierarchy**

```python
class TagStructure:
    """계층적 태그 구조"""
    
    # Level 1: Category (최대 5개)
    CATEGORIES = {
        'work': '업무 관련',
        'personal': '개인 생활',
        'learning': '학습/연구',
        'social': '소셜/대화',
        'system': '시스템/메타'
    }
    
    # Level 2: Activity Type (최대 15개)
    ACTIVITY_TYPES = {
        'create': '생성/개발',
        'fix': '수정/버그픽스',
        'plan': '계획/설계',
        'review': '리뷰/분석',
        'document': '문서화',
        'meeting': '회의/논의',
        'research': '조사/연구',
        'test': '테스트/검증',
        'deploy': '배포/릴리즈',
        'maintain': '유지보수'
    }
    
    # Level 3: Domain Tags (최대 50개, 동적)
    domain_tags = {
        # Technical
        'api', 'database', 'frontend', 'backend', 'auth',
        'performance', 'security', 'ui', 'ux', 'algorithm',
        
        # Languages/Tools
        'python', 'javascript', 'react', 'django', 'docker',
        
        # Concepts
        'bug', 'feature', 'refactor', 'optimization', 'migration',
        
        # Project specific (자동 학습)
        # ...dynamically added
    }
```

### 2. **Tag Schema**

```python
@dataclass
class MemoryTags:
    """메모리별 태그 스키마"""
    
    # 필수 태그
    category: str           # Level 1 (1개)
    activity: str          # Level 2 (1개)
    
    # 선택 태그
    domains: List[str]     # Level 3 (최대 5개)
    
    # 메타데이터
    auto_generated: bool   # AI가 생성했는지
    confidence: float      # AI 신뢰도 (0-1)
    user_verified: bool    # 사용자가 확인했는지
    
    # 추가 속성
    language: str          # 'ko', 'en', 'mixed'
    importance: float      # 중요도 (자동 계산)
    
    def to_dict(self):
        return {
            'category': self.category,
            'activity': self.activity,
            'domains': self.domains,
            'metadata': {
                'auto': self.auto_generated,
                'confidence': self.confidence,
                'verified': self.user_verified,
                'language': self.language
            }
        }
```

---

## 🤖 **AI Auto-Tagging Pipeline**

### Phase 1: Immediate Basic Tagging (동기)
```python
def quick_tag(content: str) -> Dict:
    """즉시 실행되는 기본 태깅"""
    
    # 1. Language detection
    language = detect_language(content)
    
    # 2. Keyword extraction (existing)
    keywords = extract_keywords(content)
    
    # 3. Rule-based category
    category = infer_category_from_keywords(keywords)
    
    return {
        'category': category,
        'activity': 'unknown',  # AI가 나중에 채움
        'domains': keywords[:3],
        'language': language
    }
```

### Phase 2: AI Enhancement (비동기)
```python
async def enhance_tags_with_ai(memory_id: int, content: str):
    """백그라운드에서 AI로 태그 개선"""
    
    # MCP를 통해 Claude에게 요청
    prompt = f"""
    다음 메모리에 대한 태그를 생성해주세요:
    "{content}"
    
    응답 형식:
    - category: {CATEGORIES 중 1개}
    - activity: {ACTIVITY_TYPES 중 1개}
    - domains: [관련 기술/도메인 태그 3-5개]
    - confidence: 0-1 사이 신뢰도
    """
    
    ai_tags = await mcp_client.analyze(prompt)
    
    # Update memory tags
    update_memory_tags(memory_id, ai_tags)
```

---

## 🔍 **Enhanced Search System**

### 1. **Multi-modal Search**
```python
def search_with_tags(
    query: str,
    category: Optional[str] = None,
    activity: Optional[str] = None,
    domains: Optional[List[str]] = None,
    exclude_tags: Optional[List[str]] = None
) -> List[Memory]:
    """태그 기반 고급 검색"""
    
    results = []
    
    # 1. Tag-based filtering
    if category:
        results = filter_by_category(category)
    
    if activity:
        results = filter_by_activity(results, activity)
    
    if domains:
        results = filter_by_domains(results, domains)
    
    # 2. Exclude unwanted
    if exclude_tags:
        results = exclude_by_tags(results, exclude_tags)
    
    # 3. Text search on filtered set
    if query:
        results = text_search(results, query)
    
    # 4. Rank by relevance
    return rank_results(results)
```

### 2. **Cross-language Search**
```python
def cross_language_search(query: str) -> List[Memory]:
    """언어 무관 검색"""
    
    # English query → search Korean memories
    if is_english(query):
        # Translate query to Korean
        ko_query = translate_to_korean(query)
        
        # Search both
        en_results = search_by_language(query, 'en')
        ko_results = search_by_language(ko_query, 'ko')
        
        return merge_results(en_results, ko_results)
    
    # Korean query → search English tags
    elif is_korean(query):
        # Extract concepts
        concepts = extract_concepts(query)
        
        # Map to English tags
        en_tags = map_to_english_tags(concepts)
        
        return search_by_tags(en_tags)
```

---

## 🔧 **Tag Maintenance System**

### 1. **Automatic Consolidation**
```python
class TagConsolidator:
    """태그 자동 통합 관리"""
    
    # Synonym groups
    SYNONYMS = {
        'bug': ['bugs', '버그', 'error', 'issue'],
        'auth': ['authentication', '인증', 'login', '로그인'],
        'api': ['API', 'endpoint', '엔드포인트', 'rest'],
        'db': ['database', '데이터베이스', 'DB', 'sql']
    }
    
    def consolidate_tags(self):
        """주기적 태그 통합 (일 1회)"""
        
        # 1. Merge synonyms
        for primary, synonyms in self.SYNONYMS.items():
            for synonym in synonyms:
                replace_tag(synonym, primary)
        
        # 2. Remove rare tags (사용 < 3회)
        remove_rare_tags(min_usage=3)
        
        # 3. Suggest new synonyms (AI)
        new_synonyms = detect_similar_tags()
        if new_synonyms:
            notify_user_for_approval(new_synonyms)
```

### 2. **Tag Lifecycle Management**
```python
class TagLifecycle:
    """태그 생명주기 관리"""
    
    def __init__(self):
        self.tag_stats = {}  # tag -> {count, last_used, created}
        self.max_tags = 50
    
    def on_tag_used(self, tag: str):
        """태그 사용 시 통계 업데이트"""
        if tag not in self.tag_stats:
            self.tag_stats[tag] = {
                'count': 0,
                'created': time.time(),
                'last_used': None
            }
        
        self.tag_stats[tag]['count'] += 1
        self.tag_stats[tag]['last_used'] = time.time()
        
        # Check if cleanup needed
        if len(self.tag_stats) > self.max_tags:
            self.cleanup_tags()
    
    def cleanup_tags(self):
        """오래되고 적게 쓰인 태그 정리"""
        
        # Score = usage_count * recency_factor
        scored_tags = []
        for tag, stats in self.tag_stats.items():
            recency = time.time() - stats['last_used']
            recency_factor = 1 / (1 + recency / 86400)  # Daily decay
            score = stats['count'] * recency_factor
            scored_tags.append((tag, score))
        
        # Keep top 50
        scored_tags.sort(key=lambda x: x[1], reverse=True)
        tags_to_remove = [tag for tag, _ in scored_tags[self.max_tags:]]
        
        for tag in tags_to_remove:
            self.archive_tag(tag)
```

---

## 📊 **Database Schema Updates**

### New Tables
```sql
-- Tag definitions
CREATE TABLE tag_definitions (
    tag_id INTEGER PRIMARY KEY,
    tag_name TEXT UNIQUE NOT NULL,
    tag_level INTEGER,  -- 1=category, 2=activity, 3=domain
    parent_tag TEXT,    -- For hierarchy
    usage_count INTEGER DEFAULT 0,
    last_used TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE
);

-- Memory-Tag associations
CREATE TABLE memory_tags (
    memory_id INTEGER,
    tag_id INTEGER,
    confidence REAL DEFAULT 1.0,
    added_by TEXT,  -- 'ai', 'user', 'system'
    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (memory_id, tag_id),
    FOREIGN KEY (memory_id) REFERENCES blocks(block_index),
    FOREIGN KEY (tag_id) REFERENCES tag_definitions(tag_id)
);

-- Tag synonyms
CREATE TABLE tag_synonyms (
    synonym TEXT PRIMARY KEY,
    canonical_tag_id INTEGER,
    FOREIGN KEY (canonical_tag_id) REFERENCES tag_definitions(tag_id)
);

-- Indexes for performance
CREATE INDEX idx_memory_tags_memory ON memory_tags(memory_id);
CREATE INDEX idx_memory_tags_tag ON memory_tags(tag_id);
CREATE INDEX idx_tag_usage ON tag_definitions(usage_count DESC);
```

---

## 🚀 **Implementation Roadmap**

### Phase 1: Foundation (Week 1)
```python
# 1. Update database schema
# 2. Basic tag structure
# 3. Manual tagging API

def add_memory_with_tags(content: str, tags: Optional[Dict] = None):
    """기본 태깅 지원 추가"""
    memory_id = add_memory(content)
    
    if tags:
        assign_tags(memory_id, tags)
    else:
        # Quick auto-tag
        auto_tags = quick_tag(content)
        assign_tags(memory_id, auto_tags)
    
    return memory_id
```

### Phase 2: AI Integration (Week 2)
```python
# 1. MCP integration for tagging
# 2. Async tag enhancement
# 3. Confidence scoring

async def enhance_all_untagged():
    """모든 미태그 메모리 처리"""
    untagged = get_memories_without_tags()
    
    for memory in untagged:
        await enhance_tags_with_ai(
            memory.id, 
            memory.content
        )
```

### Phase 3: Search Enhancement (Week 3)
```python
# 1. Tag-based search
# 2. Cross-language support
# 3. Advanced filtering

def search_v2(
    text_query: Optional[str] = None,
    tag_filter: Optional[TagFilter] = None
):
    """향상된 검색"""
    # Implementation
```

### Phase 4: Maintenance (Week 4)
```python
# 1. Auto-consolidation
# 2. Tag lifecycle
# 3. Analytics dashboard

def tag_maintenance_job():
    """일일 유지보수 작업"""
    consolidator.run()
    lifecycle.cleanup()
    analytics.generate_report()
```

---

## 📈 **Success Metrics**

### Quantitative
- Search precision: +30%
- Search recall: +25%
- Cross-language search: 90% accuracy
- Tag vocabulary: ≤50 active tags
- Auto-tag accuracy: >80%

### Qualitative
- User can find memories easier
- Language barrier removed
- Maintenance burden minimal
- System learns user's vocabulary

---

## 💡 **Key Innovation**

### Smart Tag Inheritance
```python
def inherit_context_tags(new_memory_id: int):
    """현재 컨텍스트의 태그 자동 상속"""
    
    active_context = get_active_context()
    recent_tags = get_recent_tags(minutes=10)
    
    # 최근 사용 태그 중 관련성 높은 것 상속
    inherited_tags = []
    for tag in recent_tags:
        if tag.usage_in_context > 0.3:
            inherited_tags.append(tag)
    
    assign_tags(new_memory_id, inherited_tags)
```

### Personalized Tag Learning
```python
def learn_user_vocabulary():
    """사용자 특화 태그 학습"""
    
    # 사용자가 자주 쓰는 태그 패턴 학습
    user_patterns = analyze_user_tagging_patterns()
    
    # 자동 태깅 시 사용자 패턴 반영
    update_auto_tagger_weights(user_patterns)
```

---

## 🎯 **Expected Outcome**

**3개월 후:**
- 모든 메모리가 체계적으로 태그됨
- 검색 효율 대폭 향상
- 언어 무관 검색 가능
- 자동 유지보수로 관리 부담 최소

**"메모리를 찾는 것이 아니라, 메모리가 나를 찾아온다"**